"""Auth routes — Flask Blueprint for /api/v1/auth endpoints.

Handles user registration, login, logout, and current-user lookup.
Session management uses Flask's built-in server-side session (session dict).

Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 9.1, 9.2, 9.3, 11.2
"""

import uuid

from flask import Blueprint, jsonify, request, session
from marshmallow import ValidationError

from app.schemas.auth_schemas import LoginSchema, RegisterSchema
from app.services.auth_service import AuthError, ConflictError
from app.services import auth_service

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_register_schema = RegisterSchema()
_login_schema = LoginSchema()


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


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account.

    Request body (JSON):
        email (str): A valid email address.
        password (str): A password of at least 8 characters.

    Returns:
        201 with ``{"id": ..., "email": ...}`` on success.
        400 if the JSON body is missing/malformed or fails schema validation.
        409 if the email address is already registered.
    """
    body = request.get_json(silent=True)
    if body is None:
        return _error_response("MALFORMED_REQUEST", "Request body must be valid JSON.")

    try:
        data = _register_schema.load(body)
    except ValidationError as exc:
        # Flatten all field-level messages into a single list.
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

    try:
        user = auth_service.register(data["email"], data["password"])
    except ConflictError as exc:
        return _error_response("EMAIL_CONFLICT", str(exc), status=409)

    return jsonify({"id": str(user.id), "email": user.email}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and create a session.

    Request body (JSON):
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        200 with ``{"id": ..., "email": ...}`` on success.
        400 if the JSON body is missing/malformed or fails schema validation.
        401 if the credentials are invalid.
    """
    body = request.get_json(silent=True)
    if body is None:
        return _error_response("MALFORMED_REQUEST", "Request body must be valid JSON.")

    try:
        data = _login_schema.load(body)
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

    try:
        user = auth_service.login(data["email"], data["password"])
    except AuthError as exc:
        return _error_response("UNAUTHORIZED", str(exc), status=401)

    # Store the user's ID and admin flag in the server-side session (Requirement 1.4, 11.2, 13.4).
    session["user_id"] = str(user.id)
    session["is_admin"] = bool(user.is_admin)

    return jsonify({"id": str(user.id), "email": user.email, "is_admin": user.is_admin}), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Invalidate the current session.

    Returns:
        200 with a success message on success.
        401 if the request is not authenticated.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    session.clear()

    return jsonify({"message": "Logged out successfully."}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    """Return the currently authenticated user's profile.

    Returns:
        200 with ``{"id": ..., "email": ...}`` on success.
        401 if the request is not authenticated or the user no longer exists.
    """
    auth_error = _require_auth()
    if auth_error:
        return auth_error

    user = auth_service.get_current_user(session["user_id"])
    if user is None:
        return _error_response(
            "SESSION_EXPIRED",
            "User not found.",
            status=401,
        )

    return jsonify({"id": str(user.id), "email": user.email, "is_admin": user.is_admin}), 200
