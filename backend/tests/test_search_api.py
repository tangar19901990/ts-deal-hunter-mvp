"""
Tests for the /search endpoint's static configuration.

These don't hit a real database — they verify the sort-option contract
(the frontend's <select id="sort-by"> values must exactly match these
keys) and that the FastAPI route is registered as expected.
"""

from app.api.search import SORT_OPTIONS
from app.main import app


def test_sort_options_match_frontend_contract():
    """frontend/js/app.js sort-by <select> sends exactly these 4 values."""
    expected = {"price_asc", "price_desc", "newest", "oldest"}
    assert set(SORT_OPTIONS.keys()) == expected


def test_search_route_is_registered():
    paths = app.openapi()["paths"]
    assert "/search" in paths


def test_search_route_only_accepts_get():
    paths = app.openapi()["paths"]
    methods = paths["/search"]
    assert "get" in methods
    assert "post" not in methods
