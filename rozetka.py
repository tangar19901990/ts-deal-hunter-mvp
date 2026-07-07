#!/usr/bin/env python3
"""
Standalone catalog scraper for Rozetka.ua.

Fetches a public category/search-result page and extracts listing data
(title, price, url, image) for one or more pages of results. This is the
"collector" half that's still missing from backend/app/collectors/ --
url_import.py only ever fetches a single, user-pasted product page and
deliberately never crawls; this script is the crawler, so it checks
robots.txt itself and rate-limits between requests.

Setup:
    pip install requests beautifulsoup4 --break-system-packages

Usage:
    python rozetka.py
    python rozetka.py "https://rozetka.com.ua/ua/notebooks/c80004/" --pages 3
    python rozetka.py <url> --out listings.json --delay 2
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.robotparser
from dataclasses import asdict, dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "TSDealHunterBot/1.0 (+catalog scraper; contact: tangar19901990 on GitHub)"
DEFAULT_CATEGORY_URL = "https://rozetka.com.ua/ua/notebooks/c80004/"
REQUEST_TIMEOUT = 10
DEFAULT_DELAY = 1.5


@dataclass
class Listing:
    external_id: str
    title: str
    price: float
    currency: str
    url: str
    image_url: str | None


class RobotsDisallowed(Exception):
    """Raised when robots.txt disallows fetching the requested URL."""


class ScrapeError(Exception):
    """Raised when a page can't be fetched or no listings can be found on it."""


def _check_robots(url: str) -> None:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except OSError:
        # robots.txt unreachable -- fail closed rather than crawl blind.
        raise RobotsDisallowed(f"Couldn't fetch {robots_url} to verify crawl permission.")
    if not rp.can_fetch(USER_AGENT, url):
        raise RobotsDisallowed(f"robots.txt disallows fetching: {url}")


def _parse_price(raw: str) -> float:
    cleaned = re.sub(r"[^\d.,]", "", raw).replace(",", ".")
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    return float(cleaned)


def _external_id_from_url(url: str) -> str:
    match = re.search(r"/p(\d+)", urlparse(url).path)
    return match.group(1) if match else url


def _from_json_ld(soup: BeautifulSoup, page_url: str) -> list[Listing]:
    """Rozetka category pages sometimes embed an ItemList JSON-LD block."""
    listings: list[Listing] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue

        items = data.get("itemListElement") if isinstance(data, dict) else None
        if not items:
            continue

        for entry in items:
            product = entry.get("item", entry) if isinstance(entry, dict) else None
            if not isinstance(product, dict):
                continue
            url = product.get("url")
            offers = product.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = offers.get("price")
            if not url or price is None:
                continue
            try:
                listings.append(
                    Listing(
                        external_id=_external_id_from_url(url),
                        title=(product.get("name") or "").strip(),
                        price=_parse_price(str(price)),
                        currency=(offers.get("priceCurrency") or "UAH").upper()[:3],
                        url=urljoin(page_url, url),
                        image_url=product.get("image"),
                    )
                )
            except ValueError:
                continue
    return listings


def _from_goods_tiles(soup: BeautifulSoup, page_url: str) -> list[Listing]:
    """Fallback: parse Rozetka's `.goods-tile` product cards directly."""
    listings: list[Listing] = []
    for tile in soup.select(".goods-tile"):
        link = tile.select_one("a.goods-tile__heading, a.goods-tile__picture")
        title_el = tile.select_one(".goods-tile__title")
        price_el = tile.select_one(".goods-tile__price-value")
        image_el = tile.select_one("img")

        if not link or not link.get("href") or not price_el:
            continue

        try:
            price = _parse_price(price_el.get_text())
        except ValueError:
            continue

        url = urljoin(page_url, link["href"])
        title = (title_el or link).get_text(strip=True)
        if not title:
            continue

        listings.append(
            Listing(
                external_id=_external_id_from_url(url),
                title=title,
                price=price,
                currency="UAH",
                url=url,
                image_url=image_el.get("src") if image_el else None,
            )
        )
    return listings


def _paginate(url: str, page: int) -> str:
    if page <= 1:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url.rstrip('/')}/page={page}/" if "?" not in url else f"{url}{separator}page={page}"


def fetch_page(session: requests.Session, url: str) -> list[Listing]:
    _check_robots(url)
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScrapeError(f"Couldn't fetch {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    return _from_json_ld(soup, url) or _from_goods_tiles(soup, url)


def scrape(category_url: str, pages: int, delay: float) -> list[Listing]:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    all_listings: list[Listing] = []
    seen_ids: set[str] = set()

    for page in range(1, pages + 1):
        page_url = _paginate(category_url, page)
        print(f"Fetching page {page}: {page_url}", file=sys.stderr)

        page_listings = fetch_page(session, page_url)
        if not page_listings:
            print(f"No listings found on page {page}, stopping.", file=sys.stderr)
            break

        new = [l for l in page_listings if l.external_id not in seen_ids]
        seen_ids.update(l.external_id for l in new)
        all_listings.extend(new)

        if page < pages:
            time.sleep(delay)

    return all_listings


def import_via_api(listings: list[Listing], api_base: str) -> None:
    """
    Feed each discovered listing into the backend's existing
    POST /listings/import — it re-fetches and parses the URL itself
    (see app/services/url_import.py), so this only ever hands it a URL,
    the same contract the frontend's manual-paste import form uses.
    """
    endpoint = f"{api_base.rstrip('/')}/listings/import"
    session = requests.Session()
    ok, failed = 0, 0

    for listing in listings:
        try:
            response = session.post(endpoint, json={"url": listing.url}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            ok += 1
        except requests.RequestException as exc:
            failed += 1
            detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
            print(f"Import failed for {listing.url}: {detail}", file=sys.stderr)

    print(f"Imported {ok}/{len(listings)} listings via {endpoint} ({failed} failed)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape a Rozetka.ua category/search page.")
    parser.add_argument(
        "url", nargs="?", default=DEFAULT_CATEGORY_URL, help="Category or search-result URL"
    )
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to crawl")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Seconds between requests")
    parser.add_argument("--out", default="rozetka_listings.json", help="Output JSON file path")
    parser.add_argument(
        "--import-api",
        metavar="API_BASE_URL",
        help="If set, POST each discovered listing's URL to <API_BASE_URL>/listings/import",
    )
    args = parser.parse_args()

    try:
        listings = scrape(args.url, args.pages, args.delay)
    except RobotsDisallowed as exc:
        print(f"Refusing to crawl: {exc}", file=sys.stderr)
        sys.exit(1)
    except ScrapeError as exc:
        print(f"Scrape failed: {exc}", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump([asdict(l) for l in listings], f, ensure_ascii=False, indent=2)

    print(f"Saved {len(listings)} listings to {args.out}")

    if args.import_api and listings:
        import_via_api(listings, args.import_api)


if __name__ == "__main__":
    main()
