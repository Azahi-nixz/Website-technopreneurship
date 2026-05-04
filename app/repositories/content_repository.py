"""Content repository — JSON file-based storage for the site content config.

Stores a single ContentConfig object in data/content.json.
"""

from datetime import datetime, timezone

from app.db import read_collection, write_collection
from app.models.content import ContentConfig

_COL = "content"

_DEFAULTS = {
    "site_title": "LUXE STORE",
    "brand_name": "Luxe Store",
    "hero_headline": "Discover Luxury Redefined",
    "hero_subheadline": "Curated premium products crafted for those who appreciate the finest things in life.",
    "nav_home_label": "Home",
    "nav_products_label": "Products",
    "nav_cart_label": "Cart",
    "nav_orders_label": "Orders",
    "footer_tagline": "Premium products for discerning customers. Quality and elegance in every item.",
    "footer_copyright": "© 2024 LUXE STORE. All rights reserved.",
    "section_heading": "Our Collection",
    "section_subheading": "Handpicked premium items",
    "cta_shop_now": "Shop Now",
    "cta_view_cart": "View Cart",
    "cta_sign_in": "Sign In",
    "empty_cart_message": "Your cart is empty.",
    "empty_orders_message": "No orders yet.",
}

# All fields that must not be empty
REQUIRED_FIELDS = list(_DEFAULTS.keys())


def _row_to_content(d: dict) -> ContentConfig:
    return ContentConfig(
        site_title=d.get("site_title", _DEFAULTS["site_title"]),
        brand_name=d.get("brand_name", _DEFAULTS["brand_name"]),
        hero_headline=d.get("hero_headline", _DEFAULTS["hero_headline"]),
        hero_subheadline=d.get("hero_subheadline", _DEFAULTS["hero_subheadline"]),
        nav_home_label=d.get("nav_home_label", _DEFAULTS["nav_home_label"]),
        nav_products_label=d.get("nav_products_label", _DEFAULTS["nav_products_label"]),
        nav_cart_label=d.get("nav_cart_label", _DEFAULTS["nav_cart_label"]),
        nav_orders_label=d.get("nav_orders_label", _DEFAULTS["nav_orders_label"]),
        footer_tagline=d.get("footer_tagline", _DEFAULTS["footer_tagline"]),
        footer_copyright=d.get("footer_copyright", _DEFAULTS["footer_copyright"]),
        section_heading=d.get("section_heading", _DEFAULTS["section_heading"]),
        section_subheading=d.get("section_subheading", _DEFAULTS["section_subheading"]),
        cta_shop_now=d.get("cta_shop_now", _DEFAULTS["cta_shop_now"]),
        cta_view_cart=d.get("cta_view_cart", _DEFAULTS["cta_view_cart"]),
        cta_sign_in=d.get("cta_sign_in", _DEFAULTS["cta_sign_in"]),
        empty_cart_message=d.get("empty_cart_message", _DEFAULTS["empty_cart_message"]),
        empty_orders_message=d.get("empty_orders_message", _DEFAULTS["empty_orders_message"]),
        updated_at=datetime.fromisoformat(d["updated_at"]) if "updated_at" in d
                   else datetime.now(timezone.utc),
    )


def _load() -> dict:
    """Load the singleton content dict, inserting defaults if absent."""
    rows = read_collection(_COL)
    if rows:
        return rows[0]
    default = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
    write_collection(_COL, [default])
    return default


def get_content() -> ContentConfig:
    """Return the active ContentConfig."""
    return _row_to_content(_load())


def update_content(fields: dict) -> ContentConfig:
    """Persist updated content fields and return the new ContentConfig."""
    row = _load()
    for key, value in fields.items():
        if key in REQUIRED_FIELDS:
            row[key] = value
    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_collection(_COL, [row])
    return _row_to_content(row)


def reset_content() -> ContentConfig:
    """Restore the ContentConfig to factory defaults."""
    row = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
    write_collection(_COL, [row])
    return _row_to_content(row)
