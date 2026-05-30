"""CSRF protection middleware for the Flask application.

Generates a per-session CSRF token and validates it on all state-changing
requests (POST, PUT, DELETE, PATCH). Login and register endpoints are exempt
because no session exists yet at that point.

Requirements: 11.3
"""

import secrets
import uuid

from flask import jsonify, request, session

CSRF_TOKEN_KEY = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
STATE_CHANGING_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Endpoints that are exempt from CSRF validation (pre-session flows).
_EXEMPT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token.

    Returns:
        A 64-character hex string produced by :func:`secrets.token_hex`.
    """
    return secrets.token_hex(32)


def get_csrf_token() -> str:
    """Return the CSRF token for the current session, creating one if absent.

    The token is stored in the server-side session under :data:`CSRF_TOKEN_KEY`.

    Returns:
        The current session's CSRF token string.
    """
    if CSRF_TOKEN_KEY not in session:
        session[CSRF_TOKEN_KEY] = generate_csrf_token()
    return session[CSRF_TOKEN_KEY]


def validate_csrf(app) -> None:
    """Register a ``before_request`` hook that validates CSRF tokens.

    The hook runs before every request and enforces the following rules:

    * Safe methods (GET, HEAD, OPTIONS, TRACE) are always allowed.
    * ``/api/v1/auth/login`` and ``/api/v1/auth/register`` are exempt because
      the client has no session (and therefore no token) yet.
    * All other state-changing requests (POST, PUT, DELETE, PATCH) must supply
      the ``X-CSRF-Token`` header whose value matches the token stored in the
      server-side session.  A missing or mismatched token returns **403** with
      the ``CSRF_INVALID`` error code.

    Args:
        app: The Flask application instance to register the hook on.
    """

    @app.before_request
    def check_csrf():  # noqa: WPS430 — nested function is intentional
        if request.method not in STATE_CHANGING_METHODS:
            return None

        if request.path in _EXEMPT_PATHS:
            return None

        session_token = session.get(CSRF_TOKEN_KEY)
        request_token = request.headers.get(CSRF_HEADER)

        # Use secrets.compare_digest to prevent timing-based attacks.
        if (
            not session_token
            or not request_token
            or not secrets.compare_digest(session_token, request_token)
        ):
            return (
                jsonify(
                    {
                        "error": {
                            "code": "CSRF_INVALID",
                            "message": "CSRF token missing or invalid.",
                            "details": [],
                            "trace_id": str(uuid.uuid4()),
                        }
                    }
                ),
                403,
            )

        return None


def get_csrf_token_endpoint(app) -> None:
    """Register a ``GET /api/v1/csrf-token`` endpoint.

    Clients call this endpoint once (e.g. on page load) to obtain a CSRF token
    that they must include as the ``X-CSRF-Token`` header on subsequent
    state-changing requests.

    Args:
        app: The Flask application instance to register the route on.
    """

    @app.route("/api/v1/csrf-token", methods=["GET"])
    def csrf_token():  # noqa: WPS430
        token = get_csrf_token()
        return jsonify({"csrf_token": token}), 200
