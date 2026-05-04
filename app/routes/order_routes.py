"""Order routes — Flask Blueprint for /api/v1/orders endpoints.

Handles placing orders (from cart or buy-now), retrieving order history, and
fetching a single order by id.  All endpoints require an authenticated session.

Requirements: 5.2, 6.1, 6.3, 6.4, 7.1, 7.2, 7.3, 7.4, 9.1, 9.2
"""

import uuid

from flask import Blueprint, jsonify, request, session
from marshmallow import ValidationError

from app.repositories import order_repository
from app.schemas.order_schemas import BuyNowSchema, OrderSchema
from app.services.product_service import NotFoundError
from app.services import order_service

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_order_schema = OrderSchema()
_orders_schema = OrderSchema(many=True)
_buy_now_schema = BuyNowSchema()


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


@orders_bp.route("", methods=["POST"])
def place_order():
    """Place an order from the authenticated user's current cart.

    Snapshots product prices at the time of order creation.  Clears the cart
    after a successful order (Requirement 7.1).

    Returns:
        201 with the serialized Order (including items) on success.
        400 if the cart is empty.
        401 if the request is not authenticated.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    user_id = uuid.UUID(session["user_id"])

    try:
        order = order_service.place_order(user_id)
    except ValueError as exc:
        return _error_response("VALIDATION_ERROR", str(exc), status=400)

    return jsonify(_order_schema.dump(order)), 201


@orders_bp.route("/buy-now", methods=["POST"])
def buy_now():
    """Purchase a single product immediately, bypassing the cart.

    Request body (JSON):
        product_id (str): UUID of the product to purchase.

    Returns:
        201 with the serialized Order on success.
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
        data = _buy_now_schema.load(body)
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
        order = order_service.buy_now(
            user_id=user_id,
            product_id=data["product_id"],
        )
    except NotFoundError as exc:
        return _error_response("NOT_FOUND", str(exc), status=404)

    return jsonify(_order_schema.dump(order)), 201


@orders_bp.route("", methods=["GET"])
def get_order_history():
    """Return the authenticated user's order history, newest first.

    Returns:
        200 with a JSON array of serialized Order objects (Requirement 7.3).
        401 if the request is not authenticated.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    user_id = uuid.UUID(session["user_id"])
    orders = order_service.get_order_history(user_id)
    return jsonify(_orders_schema.dump(orders)), 200


@orders_bp.route("/<order_id>", methods=["GET"])
def get_order(order_id: str):
    """Return a single order by id, including all its items.

    Args:
        order_id: The UUID string of the order to retrieve.

    Returns:
        200 with the serialized Order on success.
        400 if ``order_id`` is not a valid UUID.
        401 if the request is not authenticated.
        404 if no order with the given id exists.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        return _error_response(
            "VALIDATION_ERROR",
            "Invalid order id — must be a valid UUID.",
            status=400,
        )

    order = order_repository.find_by_id(oid)
    if order is None:
        return _error_response("NOT_FOUND", "Order not found.", status=404)

    return jsonify(_order_schema.dump(order)), 200
