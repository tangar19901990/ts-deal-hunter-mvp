"""Tests for Telegram bot command parsing (pure logic, no bot/DB needed)."""

from app.telegram.commands import format_saved_search, parse_watch_command


def test_parse_query_only():
    query, filters = parse_watch_command("RTX 4090")
    assert query == "RTX 4090"
    assert filters == {}


def test_parse_query_with_max_price():
    query, filters = parse_watch_command("RTX 4090 max:1200")
    assert query == "RTX 4090"
    assert filters == {"max_price": 1200.0}


def test_parse_query_with_multiple_filters():
    query, filters = parse_watch_command(
        "PlayStation 5 min:200 max:400 marketplace:ebay condition:new"
    )
    assert query == "PlayStation 5"
    assert filters == {
        "min_price": 200.0,
        "max_price": 400.0,
        "marketplace": "ebay",
        "condition": "new",
    }


def test_parse_ignores_unknown_filter_keys():
    query, filters = parse_watch_command("iPhone 16 Pro color:blue")
    # "color" isn't a recognized filter key, so it's dropped entirely
    # (not folded into the query, to avoid silently corrupting searches)
    assert query == "iPhone 16 Pro"
    assert filters == {}


def test_parse_ignores_invalid_numeric_value():
    query, filters = parse_watch_command("RTX 4090 max:cheap")
    assert query == "RTX 4090"
    assert filters == {}


def test_format_saved_search_with_filters():
    result = format_saved_search(1, "RTX 4090", {"max_price": 1200.0})
    assert result == '1. "RTX 4090" (max_price=1200.0)'


def test_format_saved_search_without_filters():
    result = format_saved_search(2, "PS5", {})
    assert result == '2. "PS5" (без фільтрів)'
