"""Admin service — privileged product management operations.

All methods in this service assume the caller has already verified that the
current session belongs to an admin user (is_admin=True).  The route layer
enforces this via the require_admin decorator before calling into this service.

Requirements: 13.3, 13.9, 13.10
"""

from decimal import Decimal
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

from app.models.product import Product, ProductImage
from app.repositories import product_repository

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""


class ValidationError(Exception):
    """Raised when input data fails validation."""


# ---------------------------------------------------------------------------
# Session check
# ---------------------------------------------------------------------------

def is_admin_session(session: dict) -> bool:
    """Return True if the session belongs to an admin user.

    Args:
        session: The Flask session dict.

    Returns:
        True if ``session["is_admin"]`` is exactly ``True``.
    """
    return session.get("is_admin") is True


# ---------------------------------------------------------------------------
# Product management
# ---------------------------------------------------------------------------

def list_all_products() -> List[Product]:
    """Return all products (active and inactive).

    Returns:
        A list of all Product instances, sorted by creation date descending.
    """
    from app.db import read_collection
    products = read_collection("products")
    result = [product_repository._dict_to_product(p) for p in products]
    result.sort(key=lambda p: p.created_at, reverse=True)
    return result


def create_product(name: str, price: Decimal, description: Optional[str] = None) -> Product:
    """Create a new product.

    Args:
        name: Product name (required, non-empty).
        price: Product price (required, non-negative).
        description: Optional product description.

    Returns:
        The newly created Product instance.

    Raises:
        ValidationError: If name is empty or price is negative.
    """
    name = (name or "").strip()
    if not name:
        raise ValidationError("Product name is required.")
    if price < 0:
        raise ValidationError("Price must be non-negative.")
    return product_repository.create_product(name, description, price)


def update_product(product_id: UUID, **fields) -> Product:
    """Update fields on an existing product.

    Args:
        product_id: UUID of the product to update.
        **fields: Keyword arguments for fields to update (name, price,
                  description, is_active).

    Returns:
        The updated Product instance.

    Raises:
        NotFoundError: If no product with the given ID exists.
        ValidationError: If updated name is empty or price is negative.
    """
    if "name" in fields:
        name = (fields["name"] or "").strip()
        if not name:
            raise ValidationError("Product name cannot be empty.")
        fields["name"] = name
    if "price" in fields and fields["price"] < 0:
        raise ValidationError("Price must be non-negative.")

    product = product_repository.update_product(product_id, **fields)
    if product is None:
        raise NotFoundError(f"Product {product_id} not found.")
    return product


def delete_product(product_id: UUID) -> None:
    """Delete a product permanently.

    Args:
        product_id: UUID of the product to delete.

    Raises:
        NotFoundError: If no product with the given ID exists.
    """
    if not product_repository.delete_product(product_id):
        raise NotFoundError(f"Product {product_id} not found.")


def add_product_image_file(
    product_id: UUID, file_data: bytes, extension: str
) -> ProductImage:
    """Save an uploaded image file and attach it to a product.

    Args:
        product_id: UUID of the product.
        file_data: Raw bytes of the image file.
        extension: File extension including the dot (e.g. ".jpg").

    Returns:
        The newly created ProductImage instance.

    Raises:
        ValidationError: If the extension is not allowed or the file is too large.
        NotFoundError: If no product with the given ID exists.
    """
    ext = extension.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type {ext!r} not allowed. Allowed: "
            + ", ".join(sorted(_ALLOWED_EXTENSIONS))
        )
    if len(file_data) > _MAX_FILE_SIZE:
        raise ValidationError(
            f"File too large (max {_MAX_FILE_SIZE // 1024 // 1024} MB)."
        )

    filename = f"{uuid4()}{ext}"
    dest = _UPLOAD_DIR / filename
    dest.write_bytes(file_data)

    image_url = f"/static/uploads/{filename}"
    img = product_repository.add_image(product_id, image_url)
    if img is None:
        dest.unlink(missing_ok=True)
        raise NotFoundError(f"Product {product_id} not found.")
    return img


def add_product_image_url(product_id: UUID, image_url: str) -> ProductImage:
    """Attach an external image URL to a product.

    Args:
        product_id: UUID of the product.
        image_url: The external image URL.

    Returns:
        The newly created ProductImage instance.

    Raises:
        ValidationError: If image_url is empty.
        NotFoundError: If no product with the given ID exists.
    """
    image_url = (image_url or "").strip()
    if not image_url:
        raise ValidationError("image_url is required.")

    img = product_repository.add_image(product_id, image_url)
    if img is None:
        raise NotFoundError(f"Product {product_id} not found.")
    return img


def remove_product_image(product_id: UUID, image_id: UUID) -> None:
    """Remove an image from a product and delete the file if it was uploaded.

    Args:
        product_id: UUID of the product.
        image_id: UUID of the image to remove.

    Raises:
        NotFoundError: If the image is not found on the product.
    """
    # Capture the URL before deletion so we can clean up the file.
    images = product_repository.get_images(product_id)
    target = next((i for i in images if i.id == image_id), None)

    if not product_repository.remove_image(product_id, image_id):
        raise NotFoundError(f"Image {image_id} not found on product {product_id}.")

    # Delete the uploaded file if it lives in our uploads folder.
    if target and target.image_url.startswith("/static/uploads/"):
        filename = target.image_url.split("/")[-1]
        file_path = _UPLOAD_DIR / filename
        file_path.unlink(missing_ok=True)
