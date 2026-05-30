"""Content service — persist and retrieve all editable site copy.

Requirements: 16.3, 16.5, 16.6
"""

from app.models.content import ContentConfig
from app.repositories import content_repository
from app.repositories.content_repository import REQUIRED_FIELDS


class ContentValidationError(Exception):
    """Raised when one or more required content fields are empty."""

    def __init__(self, message: str, empty_fields: list):
        super().__init__(message)
        self.empty_fields = empty_fields


def content_to_dict(content: ContentConfig) -> dict:
    return {
        "site_title": content.site_title,
        "brand_name": content.brand_name,
        "hero_headline": content.hero_headline,
        "hero_subheadline": content.hero_subheadline,
        "nav_home_label": content.nav_home_label,
        "nav_products_label": content.nav_products_label,
        "nav_cart_label": content.nav_cart_label,
        "nav_orders_label": content.nav_orders_label,
        "footer_tagline": content.footer_tagline,
        "footer_copyright": content.footer_copyright,
        "section_heading": content.section_heading,
        "section_subheading": content.section_subheading,
        "cta_shop_now": content.cta_shop_now,
        "cta_view_cart": content.cta_view_cart,
        "cta_sign_in": content.cta_sign_in,
        "empty_cart_message": content.empty_cart_message,
        "empty_orders_message": content.empty_orders_message,
        "updated_at": content.updated_at.isoformat(),
    }


def get_content() -> ContentConfig:
    """Return the active ContentConfig."""
    return content_repository.get_content()


def update_content(fields: dict) -> ContentConfig:
    """Update ContentConfig fields.

    Args:
        fields: A dict of field names to new values.

    Returns:
        The updated ContentConfig.

    Raises:
        ContentValidationError: If any required field is submitted as an empty string.
    """
    empty_fields = [
        key for key in REQUIRED_FIELDS
        if key in fields and (fields[key] or "").strip() == ""
    ]
    if empty_fields:
        raise ContentValidationError(
            f"Required fields cannot be empty: {', '.join(empty_fields)}",
            empty_fields=empty_fields,
        )

    # Strip whitespace from all submitted fields
    cleaned = {k: v.strip() if isinstance(v, str) else v for k, v in fields.items()}
    return content_repository.update_content(cleaned)


def reset_content() -> ContentConfig:
    """Restore the ContentConfig to factory defaults.

    Returns:
        The reset ContentConfig.
    """
    return content_repository.reset_content()
