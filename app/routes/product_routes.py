"""Product routes — Flask Blueprint for /api/v1/products endpoints.

Handles listing all active products and fetching a single product by id.
No authentication is required for these read-only endpoints.

Requirements: 3.1, 4.1, 9.1, 9.2
"""

import uuid

from flask import Blueprint, jsonify

from app.schemas.product_schemas import ProductSchema
from app.services.product_service import NotFoundError
from app.services import product_service

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_product_schema = ProductSchema()
_products_schema = ProductSchema(many=True)


def _error_response(code: str, message: str, details=None, status: int = 400):
    """Build a consistent JSON error envelope and return a Flask response tuple.

    Args:
        code: Machine-readable error code (e.g. ``NOT_FOUND``).
        message: Human-readable description safe to expose to clients.
        details: Optional list of field-level error strings.
        status: HTTP status code.

    Returns:
        A ``(Response, int)`` tuple suitable for returning from a view.
    """
    return (
        jsonify(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "details": details if details is not None else [],
                    "trace_id": str(uuid.uuid4()),
                }
            }
        ),
        status,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@products_bp.route("", methods=["GET"])
def list_products():
    """Return all active products.

    Returns:
        200 with a JSON array of serialized Product objects.
    """
    products = product_service.list_active_products()
    return jsonify(_products_schema.dump(products)), 200


@products_bp.route("/<product_id>", methods=["GET"])
def get_product(product_id: str):
    """Return a single active product by id.

    Args:
        product_id: The UUID string from the URL path.

    Returns:
        200 with the serialized Product on success.
        400 if ``product_id`` is not a valid UUID.
        404 if no active product with that id exists.
    """
    try:
        uid = uuid.UUID(product_id)
    except ValueError:
        return _error_response(
            "VALIDATION_ERROR",
            "Invalid product id — must be a valid UUID.",
            status=400,
        )

    try:
        product = product_service.get_product(uid)
    except NotFoundError as exc:
        return _error_response("NOT_FOUND", str(exc), status=404)

    return jsonify(_product_schema.dump(product)), 200
