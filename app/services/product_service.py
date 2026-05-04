"""Product service — business logic layer for product operations.

Delegates all database access to the product_repository module and raises
domain-level exceptions so that route handlers can map them to HTTP responses.

Requirements: 3.1, 4.1, 9.1, 9.2
"""

from typing import List
from uuid import UUID

from app.models.product import Product, ProductImage
from app.repositories import product_repository


class NotFoundError(Exception):
    """Raised when a requested resource does not exist or is inactive."""


def list_active_products() -> List[Product]:
    """Return all active products ordered by created_at descending.

    Delegates to product_repository.list_active().

    Returns:
        A list of Product instances where is_active=True, each with its
        images list populated, ordered newest-first.
    """
    return product_repository.list_active()


def get_product(product_id: UUID) -> Product:
    """Return the active product with the given id.

    Delegates to product_repository.find_by_id().

    Args:
        product_id: The UUID primary key of the product to fetch.

    Returns:
        A Product instance with images populated.

    Raises:
        NotFoundError: If no active product with the given id exists.
    """
    product = product_repository.find_by_id(product_id)
    if product is None:
        raise NotFoundError("Product not found.")
    return product


def get_product_images(product_id: UUID) -> List[ProductImage]:
    """Return all images for the given product ordered by display_order ASC.

    Delegates to product_repository.get_images().

    Args:
        product_id: The UUID of the product whose images to fetch.

    Returns:
        A list of ProductImage instances ordered by display_order ascending.
        Returns an empty list if the product has no images.
    """
    return product_repository.get_images(product_id)
