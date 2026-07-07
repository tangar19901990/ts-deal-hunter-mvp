"""
SavedSearch model — a persistent search a user wants monitored.

Design decision: the user identity is the Telegram chat_id, not a
separate accounts/login system. For this MVP's actual use case (get
notified in Telegram when a deal appears), the chat_id IS the user
identity — adding a parallel auth system would be pure overengineering
with zero functional benefit at this stage. If a web dashboard with
its own login is ever needed, telegram_chat_id becomes a linked
identity on a real User row rather than the primary key of "who owns
this search" — but that's a future migration, not now.

Filters are stored as JSONB rather than individual columns: the set of
filterable fields already grew once (see Listing/search endpoint) and
will likely grow again. JSONB lets this table absorb new filter types
without a migration, while the fields that matter for query planning
(query text, is_active) stay as real indexed columns.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    telegram_chat_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    query: Mapped[str] = mapped_column(String(500), nullable=False)

    # Mirrors the /search endpoint's filter params: min_price, max_price,
    # marketplace, brand, condition, category. Stored as-is so the
    # scheduler (Step 3) can pass this dict straight into the same
    # search logic the API already uses — one code path, no duplication.
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
