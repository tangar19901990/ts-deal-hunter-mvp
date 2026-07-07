"""
Search API — the core MVP feature.

GET /search?q=rtx+4090&min_price=...&max_price=...&marketplace=ebay
           &brand=...&condition=used&category=...&sort_by=price_asc

Returns the cheapest matching listings across all connected marketplaces,
deduplicated at the DB level (unique constraint on marketplace+external_id
means a collector can never insert true duplicates), sorted per request.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.listing import Listing
from app.models.marketplace import Marketplace
from app.schemas.listing import ListingOut

router = APIRouter()

SORT_OPTIONS = {
    "price_asc": Listing.price.asc(),
    "price_desc": Listing.price.desc(),
    "newest": Listing.published_at.desc(),
    "oldest": Listing.published_at.asc(),
}


@router.get("/search", response_model=list[ListingOut])
async def search_listings(
    q: str = Query(..., min_length=1, description="Product name to search for"),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    marketplace: str | None = Query(None, description="Marketplace slug, e.g. 'ebay'"),
    brand: str | None = Query(None),
    condition: str | None = Query(None),
    category: str | None = Query(None),
    sort_by: str = Query("price_asc", pattern="^(price_asc|price_desc|newest|oldest)$"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[ListingOut]:
    stmt = (
        select(Listing)
        .join(Marketplace, Listing.marketplace_id == Marketplace.id)
        .where(Listing.title.ilike(f"%{q}%"))
    )

    if min_price is not None:
        stmt = stmt.where(Listing.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Listing.price <= max_price)
    if marketplace:
        stmt = stmt.where(Marketplace.slug == marketplace)
    if brand:
        stmt = stmt.where(Listing.brand.ilike(brand))
    if condition:
        stmt = stmt.where(Listing.condition == condition)
    if category:
        stmt = stmt.where(Listing.category.ilike(category))

    stmt = stmt.order_by(SORT_OPTIONS[sort_by]).limit(limit)

    result = await db.execute(stmt)
    listings = result.scalars().all()
    return [ListingOut.from_listing(listing) for listing in listings]
