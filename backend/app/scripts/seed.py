"""
Seed script — populates a few marketplaces and sample listings so the
/search endpoint has real data to return during local development.

Run inside the container:
    docker-compose exec api python -m app.scripts.seed
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.listing import Listing
from app.models.marketplace import Marketplace

MARKETPLACES = [
    {"slug": "ebay", "name": "eBay", "base_url": "https://www.ebay.com"},
    {"slug": "olx", "name": "OLX", "base_url": "https://www.olx.ua"},
]

LISTINGS = [
    dict(
        marketplace_slug="ebay",
        external_id="ebay-rtx4090-001",
        title="NVIDIA RTX 4090 24GB Founders Edition",
        price=1249.99,
        currency="USD",
        seller="techliquidators",
        location="Berlin, DE",
        condition="used",
        brand="NVIDIA",
        category="GPU",
        url="https://www.ebay.com/itm/rtx4090-example",
        image_url=None,
        published_at=datetime(2026, 7, 5, 10, 0, tzinfo=timezone.utc),
    ),
    dict(
        marketplace_slug="olx",
        external_id="olx-xm6-001",
        title="Sony WH-1000XM6 Wireless Noise Cancelling",
        price=289.0,
        currency="USD",
        seller="audio_deals",
        location="Kyiv, UA",
        condition="new",
        brand="Sony",
        category="Headphones",
        url="https://www.olx.ua/example-xm6",
        image_url=None,
        published_at=datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc),
    ),
    dict(
        marketplace_slug="ebay",
        external_id="ebay-ps5-001",
        title="Sony PlayStation 5 Slim Disc Edition",
        price=379.5,
        currency="USD",
        seller="gamestop_outlet",
        location="Warsaw, PL",
        condition="new",
        brand="Sony",
        category="Console",
        url="https://www.ebay.com/itm/ps5-example",
        image_url=None,
        published_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
    ),
    dict(
        marketplace_slug="ebay",
        external_id="ebay-legion-001",
        title="Lenovo Legion Pro 7i 16-inch RTX 4080",
        price=1899.0,
        currency="USD",
        seller="pcworld_deals",
        location="Amsterdam, NL",
        condition="new",
        brand="Lenovo",
        category="Laptop",
        url="https://www.ebay.com/itm/legion-example",
        image_url=None,
        published_at=datetime(2026, 6, 28, 9, 15, tzinfo=timezone.utc),
    ),
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        slug_to_id = {}

        for m in MARKETPLACES:
            existing = await session.execute(
                select(Marketplace).where(Marketplace.slug == m["slug"])
            )
            obj = existing.scalar_one_or_none()
            if obj is None:
                obj = Marketplace(**m)
                session.add(obj)
                await session.flush()
                print(f"Created marketplace: {m['slug']}")
            slug_to_id[m["slug"]] = obj.id

        for item in LISTINGS:
            data = dict(item)
            slug = data.pop("marketplace_slug")

            existing = await session.execute(
                select(Listing).where(Listing.external_id == data["external_id"])
            )
            if existing.scalar_one_or_none() is not None:
                print(f"Skip (exists): {data['external_id']}")
                continue

            session.add(Listing(marketplace_id=slug_to_id[slug], **data))
            print(f"Created listing: {data['title']}")

        await session.commit()

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
