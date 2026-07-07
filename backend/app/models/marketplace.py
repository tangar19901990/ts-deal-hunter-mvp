"""
Marketplace model — represents a supported source (eBay, OLX, etc.).

Kept as a real table (not a hardcoded enum) so new marketplaces can be
added via a DB row + a collector plugin, without a schema migration.
"""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # "ebay", "olx"
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "eBay"
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
