"""
API response shape for a single listing.

Deliberately mirrors the field names the frontend already expects
(see frontend/js/app.js MOCK_RESULTS) so swapping API_BASE from empty
to a real URL requires zero frontend changes.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    price: float
    currency: str
    marketplace: str
    seller: str | None = None
    location: str | None = None
    condition: str | None = None
    brand: str | None = None
    category: str | None = None
    published_at: datetime | None = None
    url: str
    image: str | None = None

    @classmethod
    def from_listing(cls, listing) -> "ListingOut":
        """Build from an ORM Listing instance (with `marketplace` relationship loaded)."""
        return cls(
            title=listing.title,
            price=float(listing.price),
            currency=listing.currency,
            marketplace=listing.marketplace.name,
            seller=listing.seller,
            location=listing.location,
            condition=listing.condition,
            brand=listing.brand,
            category=listing.category,
            published_at=listing.published_at,
            url=listing.url,
            image=listing.image_url,
        )
