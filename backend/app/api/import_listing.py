"""
POST /listings/import — save one product by URL.

Scope: this only ever fetches the exact URL the person submits. It does
not search, does not follow links, does not crawl categories. See
app/services/url_import.py for the reasoning behind that boundary.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.listing import Listing
from app.models.marketplace import Marketplace
from app.schemas.listing import ListingOut
from app.services.url_import import ImportError as ImportPageError
from app.services.url_import import import_listing_from_url

router = APIRouter()


class ImportRequest(BaseModel):
    url: HttpUrl


@router.post("/listings/import", response_model=ListingOut)
async def import_listing(
    body: ImportRequest,
    db: AsyncSession = Depends(get_db),
) -> ListingOut:
    try:
        parsed = await import_listing_from_url(str(body.url))
    except ImportPageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Ensure the marketplace row exists
    result = await db.execute(
        select(Marketplace).where(Marketplace.slug == parsed.marketplace_slug)
    )
    marketplace = result.scalar_one_or_none()
    if marketplace is None:
        marketplace = Marketplace(
            id=uuid.uuid4(),
            slug=parsed.marketplace_slug,
            name=parsed.marketplace_name,
            base_url=str(body.url),
        )
        db.add(marketplace)
        await db.flush()

    listing = Listing(
        id=uuid.uuid4(),
        marketplace_id=marketplace.id,
        external_id=str(body.url),  # the URL itself is a stable unique key here
        title=parsed.title,
        price=parsed.price,
        currency=parsed.currency,
        url=str(body.url),
        image_url=parsed.image_url,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing, attribute_names=["marketplace"])

    return ListingOut.from_listing(listing)
