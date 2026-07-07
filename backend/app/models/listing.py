"""
Listing model — a single product offer scraped from a marketplace.

This is the core MVP entity: search, filters, and sorting all operate
directly on this table. No AI scoring, no fraud/image analysis, no
separate "product" identity table yet — that normalization is deferred
until the platform actually needs cross-listing price aggregation
(see the full architecture doc, Phase 3/5). For the search-MVP, a flat
table is simpler, faster to query, and easier to reason about.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.marketplace import Marketplace


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("marketplace_id", "external_id", name="uq_listing_source_external_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    marketplace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("marketplaces.id"), nullable=False
    )
    marketplace: Mapped["Marketplace"] = relationship(lazy="joined")

    external_id: Mapped[str] = mapped_column(String(255), nullable=False)  # ID on the source site

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    seller: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(30), nullable=True)  # new, used, ...

    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
