"""Theme repository — JSON file-based storage for the site theme config.

Stores a single ThemeConfig object in data/theme.json.
"""

from datetime import datetime, timezone
from typing import Optional

from app.db import read_collection, write_collection
from app.models.theme import ThemeConfig

_COL = "theme"

_DEFAULTS = {
    "accent_color": "#D4AF37",
    "background_color": "#0A0E1A",
    "font_family": "Inter",
}


def _row_to_theme(d: dict) -> ThemeConfig:
    return ThemeConfig(
        accent_color=d.get("accent_color", _DEFAULTS["accent_color"]),
        background_color=d.get("background_color", _DEFAULTS["background_color"]),
        font_family=d.get("font_family", _DEFAULTS["font_family"]),
        updated_at=datetime.fromisoformat(d["updated_at"]) if "updated_at" in d
                   else datetime.now(timezone.utc),
    )


def _load() -> dict:
    """Load the singleton theme dict, inserting defaults if absent."""
    rows = read_collection(_COL)
    if rows:
        return rows[0]
    # Seed defaults
    default = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
    write_collection(_COL, [default])
    return default


def get_theme() -> ThemeConfig:
    """Return the active ThemeConfig."""
    return _row_to_theme(_load())


def update_theme(
    accent_color: Optional[str] = None,
    background_color: Optional[str] = None,
    font_family: Optional[str] = None,
) -> ThemeConfig:
    """Persist updated theme fields and return the new ThemeConfig."""
    row = _load()
    if accent_color is not None:
        row["accent_color"] = accent_color
    if background_color is not None:
        row["background_color"] = background_color
    if font_family is not None:
        row["font_family"] = font_family
    row["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_collection(_COL, [row])
    return _row_to_theme(row)


def reset_theme() -> ThemeConfig:
    """Restore the ThemeConfig to factory defaults."""
    row = {**_DEFAULTS, "updated_at": datetime.now(timezone.utc).isoformat()}
    write_collection(_COL, [row])
    return _row_to_theme(row)
