"""Flask application factory.

Call :func:`create_app` with a config name (``"development"`` or
``"production"``) to obtain a fully configured Flask application instance.

The factory:
  1. Creates the Flask app and loads configuration.
  2. Configures Flask-Session with the database or Redis backend.
  3. Registers all API Blueprints under ``/api/v1/``.
  4. Registers the CSRF middleware and CSRF-token endpoint.
  5. Registers global HTTP error handlers.
  6. Registers frontend page routes that serve static HTML files.

Requirements: 9.1, 9.5, 11.1, 11.2
"""

import os

from flask import Flask, send_from_directory

from config import get_config


def create_app(config_name: str = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: ``"development"`` or ``"production"``.  When omitted the
            value of the ``FLASK_ENV`` environment variable is used, defaulting
            to ``"development"``.

    Returns:
        A fully configured :class:`flask.Flask` instance.
    """
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
    )

    # ── 1. Load configuration ────────────────────────────────────────────────
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # ── 2. Configure Flask-Session ───────────────────────────────────────────
    _configure_session(app)

    # ── 3. Register API Blueprints ───────────────────────────────────────────
    _register_blueprints(app)

    # ── 4. Register CSRF middleware and token endpoint ───────────────────────
    from app.middleware.csrf import validate_csrf, get_csrf_token_endpoint

    validate_csrf(app)
    get_csrf_token_endpoint(app)

    # ── 5. Register global error handlers ───────────────────────────────────
    from app.errors import register_error_handlers

    register_error_handlers(app)

    # ── 6. Register frontend page routes ────────────────────────────────────
    _register_page_routes(app)

    # ── 7. Seed admin user from environment variables ────────────────────────
    with app.app_context():
        _seed_admin()

    return app


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _seed_admin() -> None:
    """Create or update the admin user from ADMIN_EMAIL / ADMIN_PASSWORD env vars.

    The admin account is seeded silently — no hint of its existence is exposed
    in any public-facing page or log output (Requirement 13.1, 13.2).
    """
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()

    if not admin_email or not admin_password:
        # No admin credentials configured — skip seeding.
        return

    from app.repositories import user_repository
    from app.services.auth_service import hash_password

    existing = user_repository.find_by_email(admin_email)
    if existing is None:
        hashed = hash_password(admin_password).decode("utf-8")
        user_repository.create_user(admin_email, hashed, is_admin=True)
    elif not existing.is_admin:
        user_repository.set_admin_flag(admin_email, True)


def _configure_session(app: Flask) -> None:
    """Initialise Flask-Session with the configured backend.

    Supported ``SESSION_TYPE`` values:
    * ``"filesystem"`` — stores sessions in a local directory (dev default).
    * ``"sqlalchemy"`` — stores sessions in the configured SQL database.
    * ``"redis"`` — stores sessions in Redis (requires ``REDIS_URL``).

    Args:
        app: The Flask application instance.
    """
    session_type = app.config.get("SESSION_TYPE", "filesystem")

    if session_type == "redis":
        import redis
        from flask_session import Session

        app.config["SESSION_REDIS"] = redis.from_url(app.config["REDIS_URL"])
        Session(app)

    elif session_type == "sqlalchemy":
        try:
            from flask_sqlalchemy import SQLAlchemy
            from flask_session import Session

            db = SQLAlchemy(app)
            app.config["SESSION_SQLALCHEMY"] = db
            Session(app)
        except ImportError:
            # Flask-SQLAlchemy not installed — fall back to filesystem.
            app.logger.warning(
                "flask_sqlalchemy not installed; falling back to filesystem sessions."
            )
            app.config["SESSION_TYPE"] = "filesystem"
            from flask_session import Session

            Session(app)

    else:
        # filesystem or any other supported type
        from flask_session import Session

        Session(app)


def _register_blueprints(app: Flask) -> None:
    """Register all API Blueprints on the application.

    Args:
        app: The Flask application instance.
    """
    from app.routes.auth_routes import auth_bp
    from app.routes.product_routes import products_bp
    from app.routes.cart_routes import cart_bp
    from app.routes.order_routes import orders_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)


def _register_page_routes(app: Flask) -> None:
    """Register frontend HTML page routes.

    Non-API paths are mapped to the appropriate static HTML file so that the
    browser can navigate directly to a URL and receive the correct page.

    Route mapping (Requirement 9.5):
      ``/``                          → ``index.html``
      ``/products``                  → ``index.html``
      ``/login``                     → ``login.html``
      ``/cart``                      → ``cart.html``
      ``/orders``                    → ``orders.html``
      ``/orders/<id>/confirmation``  → ``order-confirmation.html``

    Args:
        app: The Flask application instance.
    """
    static_dir = os.path.join(app.root_path, "static")

    @app.route("/")
    @app.route("/products")
    def index():
        """Serve the product listing page."""
        return send_from_directory(static_dir, "index.html")

    @app.route("/login")
    def login_page():
        """Serve the login / register page."""
        return send_from_directory(static_dir, "login.html")

    @app.route("/cart")
    def cart_page():
        """Serve the shopping cart page."""
        return send_from_directory(static_dir, "cart.html")

    @app.route("/orders")
    def orders_page():
        """Serve the order history page."""
        return send_from_directory(static_dir, "orders.html")

    @app.route("/orders/<order_id>/confirmation")
    def order_confirmation_page(order_id: str):
        """Serve the order confirmation page.

        Args:
            order_id: The UUID of the confirmed order (passed in the URL but
                not used server-side — the frontend reads it from the path).
        """
        return send_from_directory(static_dir, "order-confirmation.html")
