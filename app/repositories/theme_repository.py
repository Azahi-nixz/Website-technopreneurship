"""Theme repository — PostgreSQL or JSON file-based storage for site theme."""

from datetime import datetime, timezone
from typing import Optional

from app.db import USE_POSTGRES
from app.models.theme import ThemeConfig

_DEFAULTS = {
    "accent_color": "#D4AF37",
    "background_color": "#0A0E1A",
    "font_family": "Inter",
}


def _row_to_theme(row) -> ThemeConfig:
    if isinstance(row, dict):
        return ThemeConfig(
            accent_color=row.get("accent_color", _DEFAULTS["accent_color"]),
            background_color=row.get("background_color", _DEFAULTS["background_color"]),
            font_family=row.get("font_family", _DEFAULTS["font_family"]),
            updated_at=datetime.fromisoformat(row["updated_at"]) if "updated_at" in row
                       else datetime.now(timezone.utc),
        )
    else:
        # pg8000 row: (id, accent_color, background_color, font_family, updated_at)
        updated_at = row[4]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        return ThemeConfig(
            accent_color=row[1] or _DEFAULTS["accent_color"],
            background_color=row[2] or _DEFAULTS["background_color"],
            font_family=row[3] or _DEFAULTS["font_family"],
            updated_at=updated_at,
        )


def get_theme() -> ThemeConfig:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, accent_color, background_color, font_family, updated_at
                FROM site_theme WHERE id = 1
            """)
            if rows:
                return _row_to_theme(rows[0])
            # Insert defaults if no row exists
            rows = conn.run("""
                INSERT INTO site_theme (id, accent_color, background_color, font_family)
                VALUES (1, :accent, :bg, :font)
                RETURNING id, accent_color, background_color, font_family, updated_at
            """, accent=_DEFAULTS["accent_color"], bg=_DEFAULTS["background_color"],
                font=_DEFAULTS["font_family"])
            return _row_to_theme(rows[0])
    else:
        from app.db import read_collection, write_collection
        rows = read_collection("theme")
        if rows:
            return _row_to_theme(rows[0])
        default = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
        write_collection("theme", [default])
        return _row_to_theme(default)


def update_theme(
    accent_color: Optional[str] = None,
    background_color: Optional[str] = None,
    font_family: Optional[str] = None,
) -> ThemeConfig:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            updates = []
            kwargs = {}
            if accent_color is not None:
                updates.append("accent_color = :accent_color")
                kwargs["accent_color"] = accent_color
            if background_color is not None:
                updates.append("background_color = :background_color")
                kwargs["background_color"] = background_color
            if font_family is not None:
                updates.append("font_family = :font_family")
                kwargs["font_family"] = font_family
            if not updates:
                return get_theme()
            updates.append("updated_at = NOW()")
            sql = f"UPDATE site_theme SET {', '.join(updates)} WHERE id = 1 RETURNING id, accent_color, background_color, font_family, updated_at"
            rows = conn.run(sql, **kwargs)
            return _row_to_theme(rows[0]) if rows else get_theme()
    else:
        from app.db import read_collection, write_collection
        rows = read_collection("theme")
        row = rows[0] if rows else {**_DEFAULTS}
        if accent_color is not None:
            row["accent_color"] = accent_color
        if background_color is not None:
            row["background_color"] = background_color
        if font_family is not None:
            row["font_family"] = font_family
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_collection("theme", [row])
        return _row_to_theme(row)


def reset_theme() -> ThemeConfig:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                UPDATE site_theme SET
                    accent_color = :accent, background_color = :bg,
                    font_family = :font, updated_at = NOW()
                WHERE id = 1
                RETURNING id, accent_color, background_color, font_family, updated_at
            """, accent=_DEFAULTS["accent_color"], bg=_DEFAULTS["background_color"],
                font=_DEFAULTS["font_family"])
            return _row_to_theme(rows[0]) if rows else get_theme()
    else:
        from app.db import write_collection
        row = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
        write_collection("theme", [row])
        return _row_to_theme(row)
