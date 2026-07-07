"""Tests for the SavedSearch model."""

import uuid

from app.models.saved_search import SavedSearch


def test_saved_search_has_expected_columns():
    columns = {c.name for c in SavedSearch.__table__.columns}
    assert columns == {
        "id",
        "telegram_chat_id",
        "query",
        "filters",
        "is_active",
        "created_at",
    }


def test_saved_search_defaults():
    search = SavedSearch(
        id=uuid.uuid4(),
        telegram_chat_id="123456789",
        query="RTX 4090",
        filters={"max_price": 1000},
    )
    assert search.query == "RTX 4090"
    assert search.filters == {"max_price": 1000}
    assert search.telegram_chat_id == "123456789"
