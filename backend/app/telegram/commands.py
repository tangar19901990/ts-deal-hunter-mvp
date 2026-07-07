"""
Parsing logic for the Telegram bot's /watch command, kept separate
from aiogram handlers so it's testable without a running bot or DB.

Command format:
    /watch <query text> [min:N] [max:N] [marketplace:slug] [brand:name] [condition:new|used] [category:name]

Example:
    /watch RTX 4090 max:1200 marketplace:ebay condition:used
"""

FILTER_KEY_MAP = {
    "min": "min_price",
    "max": "max_price",
    "marketplace": "marketplace",
    "brand": "brand",
    "condition": "condition",
    "category": "category",
}

NUMERIC_FILTERS = {"min_price", "max_price"}


def parse_watch_command(text: str) -> tuple[str, dict]:
    """
    Parse a /watch command body into (query, filters).

    Unrecognized `key:value` tokens are ignored (not treated as query
    text) so a typo in a filter key doesn't silently pollute the search
    query. Tokens without a colon are joined back into the query string.
    """
    tokens = text.strip().split()
    query_parts: list[str] = []
    filters: dict = {}

    for token in tokens:
        if ":" in token:
            key, _, value = token.partition(":")
            key = key.lower()
            if key in FILTER_KEY_MAP:
                mapped_key = FILTER_KEY_MAP[key]
                if mapped_key in NUMERIC_FILTERS:
                    try:
                        filters[mapped_key] = float(value)
                    except ValueError:
                        pass  # unparseable numeric filter - drop the token, don't pollute query
                else:
                    filters[mapped_key] = value
            # Any token containing ":" is treated as a filter attempt,
            # recognized or not, and never folded into the query text.
            continue
        query_parts.append(token)

    return " ".join(query_parts).strip(), filters


def format_saved_search(index: int, query: str, filters: dict) -> str:
    """Human-readable one-line summary for /list."""
    filter_str = ", ".join(f"{k}={v}" for k, v in filters.items()) if filters else "без фільтрів"
    return f"{index}. \"{query}\" ({filter_str})"
