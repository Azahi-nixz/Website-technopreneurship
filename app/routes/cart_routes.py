"""Cart routes — Flask Blueprint for /api/v1/cart endpoints.

Handles retrieving the cart, adding items, updating quantities, and removing
items.  All endpoints require an authenticated session.

Requirements: 5.2, 6.1, 6.3, 6.4, 9.1, 9.2
"""

import uuid

from flask import Blueprint, jsonify, request, session
from marshmallow import ValidationError

from app.schemas.cart_schemas import AddToCartSchema, CartItemSchema, UpdateCartItemSchema
from app.services.product_service import NotFoundError
from app.services import order_service

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

cart_bp = Blueprint("cart", __name__, url_prefix="/api/v1/cart")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_cart_item_schema = CartItemSchema(many=True)
_add_to_cart_schema = AddToCartSchema()
_update_cart_item_schema = UpdateCartItemSchema()


def _error_response(code: str, message: str, details=None, status: int = 400):
    """Build a consistent JSON error envelope and return a Flask response tuple.

    Args:
        code: Machine-readable error code (e.g. ``VALIDATION_ERROR``).
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


def _require_auth():
    """Return an error response if the request is not authenticated, else None.

    Returns:
        A ``(Response, int)`` tuple if unauthenticated, or ``None`` if the
        session contains a valid ``user_id``.
    """
    if not session.get("user_id"):
        return _error_response(
            "SESSION_EXPIRED",
            "Authentication required.",
            status=401,
        )
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@cart_bp.route("", methods=["GET"])
def get_cart():
    """Return the authenticated user's current cart items.

    Returns:
        200 with a JSON array of serialized CartItem objects (with nested
        product data).
        401 if the request is not authenticated.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    user_id = uuid.UUID(session["user_id"])
    items = order_service.get_cart(user_id)
    return jsonify(_cart_item_schema.dump(items)), 200


@cart_bp.route("/items", methods=["POST"])
def add_to_cart():
    """Add a product to the cart (upsert — increments quantity if already present).

    Request body (JSON):
        product_id (str): UUID of the product to add.
        quantity (int, optional): Number of units to add; defaults to 1.

    Returns:
        201 with the serialized CartItem on success.
        400 if the JSON body is missing/malformed or fails schema validation.
        401 if the request is not authenticated.
        404 if the product does not exist or is inactive.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    body = request.get_json(silent=True)
    if body is None:
        return _error_response("MALFORMED_REQUEST", "Request body must be valid JSON.")

    try:
        data = _add_to_cart_schema.load(body)
    except ValidationError as exc:
        details = [
            f"{field}: {msg}"
            for field, messages in exc.messages.items()
            for msg in messages
        ]
        return _error_response(
            "VALIDATION_ERROR",
            "Request validation failed.",
            details=details,
        )

    user_id = uuid.UUID(session["user_id"])

    try:
        item = order_service.add_to_cart(
            user_id=user_id,
            product_id=data["product_id"],
            quantity=data.get("quantity", 1),
        )
    except NotFoundError as exc:
        return _error_response("NOT_FOUND", str(exc), status=404)

    return jsonify(CartItemSchema().dump(item)), 201


@cart_bp.route("/items/<item_id>", methods=["PUT"])
def update_cart_item(item_id: str):
    """Update the quantity of a cart item.

    Args:
        item_id: The UUID string of the cart item to update.

    Request body (JSON):
        quantity (int): The new quantity (must be ≥ 1).

    Returns:
        200 with the updated serialized CartItem on success.
        400 if the JSON body is missing/malformed, fails schema validation,
            or ``item_id`` is not a valid UUID.
        401 if the request is not authenticated.
        404 if no cart item with the given id exists.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    try:
        cart_item_id = uuid.UUID(item_id)
    except ValueError:
        return _error_response(
            "VALIDATION_ERROR",
            "Invalid item id — must be a valid UUID.",
            status=400,
        )

    body = request.get_json(silent=True)
    if body is None:
        return _error_response("MALFORMED_REQUEST", "Request body must be valid JSON.")

    try:
        data = _update_cart_item_schema.load(body)
    except ValidationError as exc:
        details = [
            f"{field}: {msg}"
            for field, messages in exc.messages.items()
            for msg in messages
        ]
        return _error_response(
            "VALIDATION_ERROR",
            "Request validation failed.",
            details=details,
        )

    user_id = uuid.UUID(session["user_id"])

    try:
        item = order_service.update_cart_item(
            user_id=user_id,
            cart_item_id=cart_item_id,
            quantity=data["quantity"],
        )
    except ValueError as exc:
        return _error_response("NOT_FOUND", str(exc), status=404)

    return jsonify(CartItemSchema().dump(item)), 200


@cart_bp.route("/items/<item_id>", methods=["DELETE"])
def remove_cart_item(item_id: str):
    """Remove an item from the cart.

    Args:
        item_id: The UUID string of the cart item to remove.

    Returns:
        200 with a success message on success.
        400 if ``item_id`` is not a valid UUID.
        401 if the request is not authenticated.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    try:
        cart_item_id = uuid.UUID(item_id)
    except ValueError:
        return _error_response(
            "VALIDATION_ERROR",
            "Invalid item id — must be a valid UUID.",
            status=400,
        )

    user_id = uuid.UUID(session["user_id"])
    order_service.remove_from_cart(user_id=user_id, cart_item_id=cart_item_id)

    return jsonify({"message": "Item removed from cart."}), 200
