"""initial schema: marketplaces + listings

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketplaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "marketplace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("marketplaces.id"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
        sa.Column("seller", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("condition", sa.String(length=30), nullable=True),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("marketplace_id", "external_id", name="uq_listing_source_external_id"),
    )

    # Search/filter/sort indexes — these are exactly the query patterns the MVP search endpoint uses
    op.create_index("ix_listings_price", "listings", ["price"])
    op.create_index("ix_listings_published_at", "listings", ["published_at"])
    op.create_index("ix_listings_title_trgm", "listings", ["title"])
    op.create_index("ix_listings_brand", "listings", ["brand"])
    op.create_index("ix_listings_category", "listings", ["category"])
    op.create_index("ix_listings_condition", "listings", ["condition"])


def downgrade() -> None:
    op.drop_index("ix_listings_condition", table_name="listings")
    op.drop_index("ix_listings_category", table_name="listings")
    op.drop_index("ix_listings_brand", table_name="listings")
    op.drop_index("ix_listings_title_trgm", table_name="listings")
    op.drop_index("ix_listings_published_at", table_name="listings")
    op.drop_index("ix_listings_price", table_name="listings")
    op.drop_table("listings")
    op.drop_table("marketplaces")
