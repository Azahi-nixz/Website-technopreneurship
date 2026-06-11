"""Content repository — PostgreSQL or JSON file-based storage for site content."""

from datetime import datetime, timezone

from app.db import USE_POSTGRES
from app.models.content import ContentConfig

_DEFAULTS = {
    "site_title": "Kuryentipid ⚡ — Sun in. Power out. Comfort always.",
    "brand_name": "Kuryentipid",
    "hero_headline": "Sun in. Power out. Comfort always. ⚡",
    "hero_subheadline": "Solar-powered appliances and gadgets built for real life. Save on bills, save the planet — without sacrificing comfort.",
    "nav_home_label": "Home",
    "nav_products_label": "Products",
    "nav_cart_label": "Cart",
    "nav_orders_label": "Orders",
    "footer_tagline": "Sun in. Power out. Comfort always. — Kuryentipid brings solar energy to every home.",
    "footer_copyright": "© 2024 Kuryentipid. All rights reserved.",
    "section_heading": "⚡ Our Solar Collection",
    "section_subheading": "Sun in. Power out. Comfort always.",
    "cta_shop_now": "Shop Now ⚡",
    "cta_view_cart": "View Cart",
    "cta_sign_in": "Sign In",
    "empty_cart_message": "Your cart is empty — time to harness the sun! 🌞",
    "empty_orders_message": "No orders yet. Start your solar journey today! ✨",
}

REQUIRED_FIELDS = list(_DEFAULTS.keys())


def _row_to_content(row) -> ContentConfig:
    if isinstance(row, dict):
        d = row
    else:
        # pg8000 row: columns in insertion order
        cols = [
            "id", "site_title", "brand_name", "hero_headline", "hero_subheadline",
            "nav_home_label", "nav_products_label", "nav_cart_label", "nav_orders_label",
            "footer_tagline", "footer_copyright", "section_heading", "section_subheading",
            "cta_shop_now", "cta_view_cart", "cta_sign_in",
            "empty_cart_message", "empty_orders_message", "updated_at"
        ]
        d = dict(zip(cols, row))

    updated_at = d.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    elif updated_at is None:
        updated_at = datetime.now(timezone.utc)

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
        updated_at=updated_at,
    )


def get_content() -> ContentConfig:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, site_title, brand_name, hero_headline, hero_subheadline,
                       nav_home_label, nav_products_label, nav_cart_label, nav_orders_label,
                       footer_tagline, footer_copyright, section_heading, section_subheading,
                       cta_shop_now, cta_view_cart, cta_sign_in,
                       empty_cart_message, empty_orders_message, updated_at
                FROM site_content WHERE id = 1
            """)
            if rows:
                return _row_to_content(rows[0])
            return _row_to_content(_DEFAULTS)
    else:
        from app.db import read_collection, write_collection
        rows = read_collection("content")
        if rows:
            return _row_to_content(rows[0])
        default = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
        write_collection("content", [default])
        return _row_to_content(default)


def update_content(fields: dict) -> ContentConfig:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            updates = ["updated_at = NOW()"]
            kwargs = {}
            for key, value in fields.items():
                if key in REQUIRED_FIELDS:
                    updates.append(f"{key} = :{key}")
                    kwargs[key] = value
            if len(updates) == 1:
                return get_content()
            sql = f"UPDATE site_content SET {', '.join(updates)} WHERE id = 1 RETURNING id, site_title, brand_name, hero_headline, hero_subheadline, nav_home_label, nav_products_label, nav_cart_label, nav_orders_label, footer_tagline, footer_copyright, section_heading, section_subheading, cta_shop_now, cta_view_cart, cta_sign_in, empty_cart_message, empty_orders_message, updated_at"
            rows = conn.run(sql, **kwargs)
            return _row_to_content(rows[0]) if rows else get_content()
    else:
        from app.db import read_collection, write_collection
        rows = read_collection("content")
        row = rows[0] if rows else {**_DEFAULTS}
        for key, value in fields.items():
            if key in REQUIRED_FIELDS:
                row[key] = value
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_collection("content", [row])
        return _row_to_content(row)


def reset_content() -> ContentConfig:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            kwargs = {k: v for k, v in _DEFAULTS.items()}
            set_clauses = [f"{k} = :{k}" for k in _DEFAULTS] + ["updated_at = NOW()"]
            sql = f"UPDATE site_content SET {', '.join(set_clauses)} WHERE id = 1 RETURNING id, site_title, brand_name, hero_headline, hero_subheadline, nav_home_label, nav_products_label, nav_cart_label, nav_orders_label, footer_tagline, footer_copyright, section_heading, section_subheading, cta_shop_now, cta_view_cart, cta_sign_in, empty_cart_message, empty_orders_message, updated_at"
            rows = conn.run(sql, **kwargs)
            return _row_to_content(rows[0]) if rows else get_content()
    else:
        from app.db import write_collection
        row = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
        write_collection("content", [row])
        return _row_to_content(row)
