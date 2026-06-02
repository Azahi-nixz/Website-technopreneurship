"""Admin routes — product management, theme config, and content config.

All endpoints under /api/v1/admin/ require a valid admin session (is_admin=True).
Unauthenticated or non-admin requests receive a 403 Forbidden response.

Public read-only endpoints:
  GET /api/v1/theme   — active ThemeConfig (no auth required)
  GET /api/v1/content — active ContentConfig (no auth required)

Requirements: 13.3, 13.6, 13.9, 13.10, 14.2, 14.4, 14.7, 16.3, 16.5, 16.6
"""

import functools
import uuid
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, session

from app.services import admin_service
from app.services.admin_service import NotFoundError, ValidationError

admin_bp = Blueprint("admin", __name__)

# Where uploaded images are stored — resolved lazily to support read-only
# filesystems (Vercel). Import _UPLOAD_DIR from admin_service so there's
# a single source of truth.
from app.services.admin_service import _UPLOAD_DIR  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _err(code: str, message: str, status: int = 400, details=None):
    return (
        jsonify({
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
                "trace_id": str(uuid.uuid4()),
            }
        }),
        status,
    )


def require_admin(f):
    """Decorator that returns 403 if the session is not an admin session."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not admin_service.is_admin_session(session):
            return _err("FORBIDDEN", "Admin access required.", status=403)
        return f(*args, **kwargs)
    return decorated


def _product_to_dict(product) -> dict:
    return {
        "id": str(product.id),
        "name": product.name,
        "description": product.description,
        "price": str(product.price),
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat(),
        "images": [
            {
                "id": str(img.id),
                "image_url": img.image_url,
                "display_order": img.display_order,
            }
            for img in product.images
        ],
    }


# ---------------------------------------------------------------------------
# Admin — Product Management
# ---------------------------------------------------------------------------

@admin_bp.route("/api/v1/admin/products", methods=["GET"])
@require_admin
def list_all_products():
    """Return all products (active and inactive)."""
    products = admin_service.list_all_products()
    return jsonify([_product_to_dict(p) for p in products]), 200


@admin_bp.route("/api/v1/admin/products", methods=["POST"])
@require_admin
def create_product():
    """Create a new product."""
    body = request.get_json(silent=True)
    if not body:
        return _err("MALFORMED_REQUEST", "Request body must be valid JSON.")

    name = (body.get("name") or "").strip()
    if not name:
        return _err("VALIDATION_ERROR", "Product name is required.")

    try:
        price = Decimal(str(body.get("price", "0")))
        if price < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        return _err("VALIDATION_ERROR", "Price must be a non-negative number.")

    description = (body.get("description") or "").strip() or None

    try:
        product = admin_service.create_product(name, price, description)
    except ValidationError as exc:
        return _err("VALIDATION_ERROR", str(exc))

    return jsonify(_product_to_dict(product)), 201


@admin_bp.route("/api/v1/admin/products/<product_id>", methods=["PUT"])
@require_admin
def update_product(product_id: str):
    """Update an existing product's fields."""
    try:
        pid = uuid.UUID(product_id)
    except ValueError:
        return _err("VALIDATION_ERROR", "Invalid product id.")

    body = request.get_json(silent=True)
    if not body:
        return _err("MALFORMED_REQUEST", "Request body must be valid JSON.")

    fields = {}
    if "name" in body:
        name = (body["name"] or "").strip()
        if not name:
            return _err("VALIDATION_ERROR", "Product name cannot be empty.")
        fields["name"] = name
    if "description" in body:
        fields["description"] = (body["description"] or "").strip() or None
    if "price" in body:
        try:
            price = Decimal(str(body["price"]))
            if price < 0:
                raise ValueError
            fields["price"] = price
        except (InvalidOperation, ValueError):
            return _err("VALIDATION_ERROR", "Price must be a non-negative number.")
    if "is_active" in body:
        fields["is_active"] = bool(body["is_active"])

    try:
        product = admin_service.update_product(pid, **fields)
    except NotFoundError:
        return _err("NOT_FOUND", "Product not found.", status=404)
    except ValidationError as exc:
        return _err("VALIDATION_ERROR", str(exc))

    return jsonify(_product_to_dict(product)), 200


@admin_bp.route("/api/v1/admin/products/<product_id>", methods=["DELETE"])
@require_admin
def delete_product(product_id: str):
    """Permanently delete a product."""
    try:
        pid = uuid.UUID(product_id)
    except ValueError:
        return _err("VALIDATION_ERROR", "Invalid product id.")

    try:
        admin_service.delete_product(pid)
    except NotFoundError:
        return _err("NOT_FOUND", "Product not found.", status=404)

    return jsonify({"message": "Product deleted."}), 200


@admin_bp.route("/api/v1/admin/products/<product_id>/images", methods=["POST"])
@require_admin
def upload_image(product_id: str):
    """Upload an image file or attach an external URL to a product."""
    try:
        pid = uuid.UUID(product_id)
    except ValueError:
        return _err("VALIDATION_ERROR", "Invalid product id.")

    # URL-based (external link)
    if request.is_json:
        body = request.get_json(silent=True) or {}
        image_url = (body.get("image_url") or "").strip()
        try:
            img = admin_service.add_product_image_url(pid, image_url)
        except ValidationError as exc:
            return _err("VALIDATION_ERROR", str(exc))
        except NotFoundError:
            return _err("NOT_FOUND", "Product not found.", status=404)
        return jsonify({
            "id": str(img.id),
            "image_url": img.image_url,
            "display_order": img.display_order,
        }), 201

    # File upload
    if "image" not in request.files:
        return _err("VALIDATION_ERROR", "No image file provided. Use field name 'image'.")

    file = request.files["image"]
    if not file.filename:
        return _err("VALIDATION_ERROR", "Empty filename.")

    ext = Path(file.filename).suffix.lower()
    file_data = file.read()

    try:
        img = admin_service.add_product_image_file(pid, file_data, ext)
    except ValidationError as exc:
        return _err("VALIDATION_ERROR", str(exc))
    except NotFoundError:
        return _err("NOT_FOUND", "Product not found.", status=404)

    return jsonify({
        "id": str(img.id),
        "image_url": img.image_url,
        "display_order": img.display_order,
    }), 201


@admin_bp.route("/api/v1/admin/products/<product_id>/images/<image_id>", methods=["DELETE"])
@require_admin
def remove_image(product_id: str, image_id: str):
    """Remove an image from a product."""
    try:
        pid = uuid.UUID(product_id)
        iid = uuid.UUID(image_id)
    except ValueError:
        return _err("VALIDATION_ERROR", "Invalid id.")

    try:
        admin_service.remove_product_image(pid, iid)
    except NotFoundError:
        return _err("NOT_FOUND", "Image not found.", status=404)

    return jsonify({"message": "Image removed."}), 200


# ---------------------------------------------------------------------------
# Admin — Theme Configuration
# ---------------------------------------------------------------------------

@admin_bp.route("/api/v1/admin/theme", methods=["GET"])
@require_admin
def get_theme_admin():
    """Retrieve the active ThemeConfig (admin)."""
    from app.services import theme_service
    theme = theme_service.get_theme()
    return jsonify(theme_service.theme_to_dict(theme)), 200


@admin_bp.route("/api/v1/admin/theme", methods=["PUT"])
@require_admin
def update_theme():
    """Update the ThemeConfig (partial update supported)."""
    from app.services import theme_service
    body = request.get_json(silent=True)
    if not body:
        return _err("MALFORMED_REQUEST", "Request body must be valid JSON.")

    try:
        theme = theme_service.update_theme(
            accent_color=body.get("accent_color"),
            background_color=body.get("background_color"),
            font_family=body.get("font_family"),
        )
    except theme_service.ThemeValidationError as exc:
        return _err("VALIDATION_ERROR", str(exc))

    return jsonify(theme_service.theme_to_dict(theme)), 200


@admin_bp.route("/api/v1/admin/theme/reset", methods=["POST"])
@require_admin
def reset_theme():
    """Reset the ThemeConfig to defaults."""
    from app.services import theme_service
    theme = theme_service.reset_theme()
    return jsonify(theme_service.theme_to_dict(theme)), 200


# Public read-only theme endpoint (no auth required)
@admin_bp.route("/api/v1/theme", methods=["GET"])
def get_theme_public():
    """Return the active ThemeConfig for CSS application (public)."""
    from app.services import theme_service
    theme = theme_service.get_theme()
    return jsonify(theme_service.theme_to_dict(theme)), 200


# ---------------------------------------------------------------------------
# Admin — Content Configuration
# ---------------------------------------------------------------------------

@admin_bp.route("/api/v1/admin/content", methods=["GET"])
@require_admin
def get_content_admin():
    """Retrieve the active ContentConfig (admin)."""
    from app.services import content_service
    content = content_service.get_content()
    return jsonify(content_service.content_to_dict(content)), 200


@admin_bp.route("/api/v1/admin/content", methods=["PUT"])
@require_admin
def update_content():
    """Update ContentConfig fields."""
    from app.services import content_service
    body = request.get_json(silent=True)
    if not body:
        return _err("MALFORMED_REQUEST", "Request body must be valid JSON.")

    try:
        content = content_service.update_content(body)
    except content_service.ContentValidationError as exc:
        return _err("VALIDATION_ERROR", str(exc), details=exc.empty_fields)

    return jsonify(content_service.content_to_dict(content)), 200


@admin_bp.route("/api/v1/admin/content/reset", methods=["POST"])
@require_admin
def reset_content():
    """Reset the ContentConfig to defaults."""
    from app.services import content_service
    content = content_service.reset_content()
    return jsonify(content_service.content_to_dict(content)), 200


# Public read-only content endpoint (no auth required)
@admin_bp.route("/api/v1/content", methods=["GET"])
def get_content_public():
    """Return the active ContentConfig for page rendering (public)."""
    from app.services import content_service
    content = content_service.get_content()
    return jsonify(content_service.content_to_dict(content)), 200


# ---------------------------------------------------------------------------
# Admin — Orders Overview
# ---------------------------------------------------------------------------

@admin_bp.route("/api/v1/admin/orders", methods=["GET"])
@require_admin
def list_all_orders():
    """Return all orders across all users, with customer email and items."""
    from app.db import read_collection

    orders = read_collection("orders")
    users_list = read_collection("users")
    products_list = read_collection("products")

    # Quick lookup maps
    user_map = {u["id"]: u["email"] for u in users_list}
    product_map = {p["id"]: p["name"] for p in products_list}

    result = []
    for o in sorted(orders, key=lambda x: x.get("created_at", ""), reverse=True):
        result.append({
            "id": o["id"],
            "customer_email": user_map.get(o.get("user_id"), "Unknown"),
            "total_amount": str(o.get("total_amount", "0")),
            "status": o.get("status", "pending"),
            "created_at": o.get("created_at", ""),
            "items": [
                {
                    "product_id": item.get("product_id"),
                    "product_name": product_map.get(item.get("product_id", ""), "Deleted product"),
                    "quantity": item.get("quantity", 1),
                    "unit_price": str(item.get("unit_price", "0")),
                }
                for item in o.get("items", [])
            ],
        })
    return jsonify(result), 200
