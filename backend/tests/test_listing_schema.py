"""
Unit tests for ListingOut.from_listing().

Uses SimpleNamespace instead of real ORM objects/DB — this keeps the
test fast and dependency-free while still verifying the exact field
mapping the frontend relies on.
"""

from types import SimpleNamespace

from app.schemas.listing import ListingOut


def _fake_listing(**overrides):
    defaults = dict(
        title="NVIDIA RTX 4090 24GB",
        price=1249.99,
        currency="USD",
        marketplace=SimpleNamespace(name="eBay"),
        seller="techliquidators",
        location="Berlin, DE",
        condition="used",
        brand="NVIDIA",
        category="GPU",
        published_at=None,
        url="https://www.ebay.com/itm/example",
        image_url=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_from_listing_maps_marketplace_name_correctly():
    listing = _fake_listing()
    out = ListingOut.from_listing(listing)

    assert out.marketplace == "eBay"
    assert out.title == "NVIDIA RTX 4090 24GB"
    assert out.price == 1249.99
    assert out.currency == "USD"
    assert out.brand == "NVIDIA"


def test_from_listing_maps_image_url_to_image_field():
    listing = _fake_listing(image_url="https://example.com/photo.jpg")
    out = ListingOut.from_listing(listing)

    assert out.image == "https://example.com/photo.jpg"


def test_from_listing_handles_optional_fields_as_none():
    listing = _fake_listing(seller=None, location=None, condition=None)
    out = ListingOut.from_listing(listing)

    assert out.seller is None
    assert out.location is None
    assert out.condition is None
