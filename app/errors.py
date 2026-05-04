"""Global HTTP error handlers for the Flask application.

All handlers return the standard JSON error envelope defined in the design:

.. code-block:: json

    {
        "error": {
            "code": "...",
            "message": "...",
            "details": [],
            "trace_id": "uuid-v4-string"
        }
    }

500 errors are additionally logged with the full stack trace and the
``trace_id`` so that support staff can correlate client-reported IDs with
server logs.

Requirements: 7.5, 9.2, 9.3, 11.3
"""

import logging
import uuid

from flask import jsonify

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, details=None, trace_id: str = None):
    """Build the standard JSON error envelope.

    Args:
        code: Machine-readable error code (e.g. ``NOT_FOUND``).
        message: Human-readable, client-safe description.
        details: Optional list of field-level error strings.
        trace_id: Optional pre-generated trace ID; a new UUID is created when
            omitted.

    Returns:
        A dict suitable for passing to :func:`flask.jsonify`.
    """
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details if details is not None else [],
            "trace_id": trace_id if trace_id is not None else str(uuid.uuid4()),
        }
    }


def register_error_handlers(app) -> None:
    """Register global HTTP error handlers on the Flask application.

    Handlers are registered for status codes 400, 401, 403, 404, 409, and 500.
    Each handler returns the standard JSON error envelope.  The 500 handler
    additionally logs the full exception with a ``trace_id`` for server-side
    correlation.

    Args:
        app: The Flask application instance to register the handlers on.
    """

    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 Bad Request — malformed or unparseable request body."""
        return (
            jsonify(_error_body("MALFORMED_REQUEST", "The request could not be understood by the server.")),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(e):
        """Handle 401 Unauthorized — missing or invalid authentication."""
        return (
            jsonify(_error_body("UNAUTHORIZED", "Authentication is required to access this resource.")),
            401,
        )

    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden — authenticated but not permitted."""
        return (
            jsonify(_error_body("FORBIDDEN", "You do not have permission to perform this action.")),
            403,
        )

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 Not Found — resource or route does not exist."""
        return (
            jsonify(_error_body("NOT_FOUND", "The requested resource could not be found.")),
            404,
        )

    @app.errorhandler(409)
    def conflict(e):
        """Handle 409 Conflict — request conflicts with current server state."""
        return (
            jsonify(_error_body("CONFLICT", "The request conflicts with the current state of the resource.")),
            409,
        )

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 Internal Server Error — unexpected server-side failure.

        Logs the full exception stack trace alongside a ``trace_id`` so that
        the error can be correlated with the client-facing response.
        """
        trace_id = str(uuid.uuid4())
        logger.error(
            "Internal server error [trace_id=%s]",
            trace_id,
            exc_info=True,
        )
        return (
            jsonify(
                _error_body(
                    "INTERNAL_ERROR",
                    "An unexpected error occurred. Please try again later.",
                    trace_id=trace_id,
                )
            ),
            500,
        )
