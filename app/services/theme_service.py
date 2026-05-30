"""Theme service — persist and retrieve the site's font and color palette.

Requirements: 14.2, 14.4, 14.7
"""

import re
from typing import Optional

from app.models.theme import ThemeConfig
from app.repositories import theme_repository

# Hex color pattern: #RGB or #RRGGBB
_HEX_RE = re.compile(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$")


class ThemeValidationError(Exception):
    """Raised when a hex color value fails validation."""


def _validate_hex(value: str, field: str) -> None:
    if not _HEX_RE.match(value):
        raise ThemeValidationError(
            f"Invalid hex color for {field!r}: {value!r}. "
            "Expected format: #RRGGBB or #RGB."
        )


def theme_to_dict(theme: ThemeConfig) -> dict:
    return {
        "accent_color": theme.accent_color,
        "background_color": theme.background_color,
        "font_family": theme.font_family,
        "updated_at": theme.updated_at.isoformat(),
    }


def get_theme() -> ThemeConfig:
    """Return the active ThemeConfig."""
    return theme_repository.get_theme()


def update_theme(
    accent_color: Optional[str] = None,
    background_color: Optional[str] = None,
    font_family: Optional[str] = None,
) -> ThemeConfig:
    """Update the ThemeConfig with the provided values.

    Args:
        accent_color: Optional hex color string for the accent color.
        background_color: Optional hex color string for the background.
        font_family: Optional font family name.

    Returns:
        The updated ThemeConfig.

    Raises:
        ThemeValidationError: If any hex color value is invalid.
    """
    if accent_color is not None:
        _validate_hex(accent_color, "accent_color")
    if background_color is not None:
        _validate_hex(background_color, "background_color")

    return theme_repository.update_theme(
        accent_color=accent_color,
        background_color=background_color,
        font_family=font_family,
    )


def reset_theme() -> ThemeConfig:
    """Restore the ThemeConfig to factory defaults.

    Defaults: accent_color=#D4AF37, background_color=#0A0E1A, font_family=Inter.

    Returns:
        The reset ThemeConfig.
    """
    return theme_repository.reset_theme()
