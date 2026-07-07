"""Tests for the price-string parser used by single-page URL import."""

from app.services.url_import import _marketplace_from_url, _parse_price


def test_parse_price_simple():
    assert _parse_price("379.50") == 379.50


def test_parse_price_with_currency_symbol():
    assert _parse_price("12 500 грн") == 12500.0


def test_parse_price_with_comma_decimal():
    assert _parse_price("289,99") == 289.99


def test_marketplace_from_known_domain():
    slug, name = _marketplace_from_url("https://www.olx.ua/d/uk/obyavlenie/example")
    assert slug == "olx"
    assert name == "OLX"


def test_marketplace_from_unknown_domain_derives_slug():
    slug, name = _marketplace_from_url("https://example-shop.com.ua/item/1")
    assert slug == "example-shop-com-ua"
