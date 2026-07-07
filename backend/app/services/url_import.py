"""
Single-page product import.

IMPORTANT scope boundary: this fetches exactly one URL the person
explicitly pasted in — it never crawls search results, category pages,
or follows links. That distinction matters: OLX's robots.txt disallows
automated access to */search/*, but a single product page fetched
because a human asked for that specific page is a different, and much
more defensible, thing (similar to how Telegram/Facebook link-preview
bots work).

Parsing strategy (best-effort, in order):
1. JSON-LD schema.org Product block (most reliable, used by most
   modern storefronts including OLX, Prom, Rozetka, eBay)
2. OpenGraph / product meta tags (title, image, price)
"""

import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "TSDealHunterBot/1.0 (+single-page import; contact: tangar19901990 on GitHub)"

KNOWN_MARKETPLACES = {
    "olx.ua": ("olx", "OLX"),
    "www.olx.ua": ("olx", "OLX"),
    "prom.ua": ("prom", "Prom.ua"),
    "www.prom.ua": ("prom", "Prom.ua"),
    "rozetka.com.ua": ("rozetka", "Rozetka"),
    "www.rozetka.com.ua": ("rozetka", "Rozetka"),
    "ebay.com": ("ebay", "eBay"),
    "www.ebay.com": ("ebay", "eBay"),
}


@dataclass
class ImportedListing:
    title: str
    price: float
    currency: str
    image_url: str | None
    marketplace_slug: str
    marketplace_name: str


class ImportError(Exception):
    """Raised when the page can't be fetched or no price/title can be found."""


def _marketplace_from_url(url: str) -> tuple[str, str]:
    host = urlparse(url).netloc.lower()
    if host in KNOWN_MARKETPLACES:
        return KNOWN_MARKETPLACES[host]
    # Unknown site: derive a slug from the domain so it still works,
    # just without a friendly display name.
    slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-") or "unknown"
    return slug, host


def _parse_price(raw: str) -> float:
    cleaned = re.sub(r"[^\d.,]", "", raw).replace(",", ".")
    # Handle "1.234.56" style thousand separators by keeping only the last dot
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    return float(cleaned)


def _try_json_ld(soup: BeautifulSoup) -> dict | None:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue

        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            if item.get("@type") == "Product" or "Product" in str(item.get("@type", "")):
                offers = item.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = offers.get("price") or offers.get("lowPrice")
                if price is None:
                    continue
                return {
                    "title": item.get("name"),
                    "image": item.get("image"),
                    "price": price,
                    "currency": offers.get("priceCurrency", "UAH"),
                }
    return None


def _try_opengraph(soup: BeautifulSoup) -> dict | None:
    def meta(*names: str) -> str | None:
        for name in names:
            tag = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
            if tag and tag.get("content"):
                return tag["content"]
        return None

    title = meta("og:title", "twitter:title")
    price = meta("product:price:amount", "og:price:amount")
    currency = meta("product:price:currency", "og:price:currency") or "UAH"
    image = meta("og:image", "twitter:image")

    if not title or not price:
        return None

    return {"title": title, "image": image, "price": price, "currency": currency}


async def import_listing_from_url(url: str) -> ImportedListing:
    """
    Fetch the single page at `url` and extract product info.
    Raises ImportError with a human-readable message on any failure.
    """
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=10.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ImportError(f"Couldn't fetch that page: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")

    data = _try_json_ld(soup) or _try_opengraph(soup)
    if data is None:
        raise ImportError(
            "Couldn't find a product title/price on that page. "
            "This site's page structure may not be supported."
        )

    try:
        price = _parse_price(str(data["price"]))
    except (ValueError, KeyError) as exc:
        raise ImportError("Found the page but couldn't parse a valid price.") from exc

    slug, name = _marketplace_from_url(url)

    return ImportedListing(
        title=data["title"].strip(),
        price=price,
        currency=(data.get("currency") or "UAH").upper()[:3],
        image_url=data.get("image"),
        marketplace_slug=slug,
        marketplace_name=name,
    )
