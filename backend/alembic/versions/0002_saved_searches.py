"""add saved_searches table

Revision ID: 0002_saved_searches
Revises: 0001_initial
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_saved_searches"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=False),
        sa.Column("filters", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_saved_searches_telegram_chat_id", "saved_searches", ["telegram_chat_id"])


def downgrade() -> None:
    op.drop_index("ix_saved_searches_telegram_chat_id", table_name="saved_searches")
    op.drop_table("saved_searches")
