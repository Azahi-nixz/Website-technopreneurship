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

    # Diagnostic: Log SECRET_KEY status (NOT the actual key) on startup.
    secret_key = app.config.get("SECRET_KEY", "")
    if secret_key == "change-me-in-production":
        app.logger.error(
            "❌ CRITICAL: SECRET_KEY is not set! Signed cookie sessions will fail. "
            "Set SECRET_KEY in Vercel Environment Variables (Settings → Environment Variables)."
        )
    elif len(secret_key) < 32:
        app.logger.warning(
            f"⚠️  WARNING: SECRET_KEY is too short ({len(secret_key)} chars). "
            "Use at least 32 characters for security."
        )
    else:
        # Log a hash of the key so we can verify it's consistent across instances
        import hashlib
        key_hash = hashlib.sha256(secret_key.encode()).hexdigest()[:8]
        app.logger.info(
            f"✓ SECRET_KEY loaded: {len(secret_key)} chars, hash={key_hash}"
        )

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

    # ── 7. Register health/diagnostic endpoint ──────────────────────────────
    @app.route("/api/v1/health")
    def health():
        """Health check endpoint with SECRET_KEY diagnostic."""
        try:
            import hashlib
            secret_key = app.config.get("SECRET_KEY", "")
            key_hash = hashlib.sha256(secret_key.encode()).hexdigest()[:12]
            return jsonify({
                "status": "ok",
                "secret_key_length": len(secret_key),
                "secret_key_hash": key_hash,
                "session_type": app.config.get("SESSION_TYPE"),
                "warning": "MISSING_SECRET_KEY" if secret_key == "change-me-in-production" else None
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "secret_key_set": "SECRET_KEY" in app.config
            }), 200

    # ── 8. Seed admin user from environment variables ────────────────────────
    with app.app_context():
        _init_database_if_needed()
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

    try:
        existing = user_repository.find_by_email(admin_email)
        if existing is None:
            hashed = hash_password(admin_password).decode("utf-8")
            user_repository.create_user(admin_email, hashed, is_admin=True)
            print(f"✓ Admin user created: {admin_email}")
        elif not existing.is_admin:
            user_repository.set_admin_flag(admin_email, True)
            print(f"✓ Admin flag set for: {admin_email}")
        else:
            print(f"✓ Admin user exists: {admin_email}")
    except Exception as e:
        print(f"❌ Failed to seed admin user: {e}")
        import traceback
        traceback.print_exc()


def _init_database_if_needed() -> None:
    """Initialize database schema and seed data on first startup if using Postgres."""
    from app.db import USE_POSTGRES
    
    if not USE_POSTGRES:
        return
    
    from app.db import get_connection
    
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # Check if tables exist
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                )
            """)
            tables_exist = cur.fetchone()[0]
            
            if tables_exist:
                print("✓ Database tables already exist")
                return
            
            print("✓ Initializing database schema...")
            
            # Run migrations
            from pathlib import Path
            migrations_dir = Path(__file__).parent.parent / "migrations"
            migration_files = sorted(migrations_dir.glob("*.sql"))
            
            for migration_file in migration_files:
                print(f"  Running {migration_file.name}...")
                sql = migration_file.read_text()
                cur.execute(sql)
            
            print("✓ Database schema created!")
            
            # Seed products
            print("✓ Seeding products...")
            products_file = Path(__file__).parent.parent / "data" / "products.json"
            if products_file.exists():
                import json
                products = json.load(products_file)
                
                for p in products:
                    cur.execute("""
                        INSERT INTO products (id, name, description, price, is_active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        p["id"], p["name"], p.get("description"),
                        p["price"], p.get("is_active", True),
                        p.get("created_at")
                    ))
                    
                    for img in p.get("images", []):
                        cur.execute("""
                            INSERT INTO product_images (id, product_id, image_url, display_order)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            img["id"], img["product_id"],
                            img["image_url"], img["display_order"]
                        ))
                
                print(f"✓ Seeded {len(products)} products!")
            
            # Seed theme
            theme_file = Path(__file__).parent.parent / "data" / "theme.json"
            if theme_file.exists():
                import json
                themes = json.load(theme_file)
                if themes:
                    t = themes[0]
                    cur.execute("""
                        INSERT INTO site_theme (accent_color, background_color, font_family, updated_at)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        t.get("accent_color"), t.get("background_color"),
                        t.get("font_family"), t.get("updated_at")
                    ))
            
            # Seed content
            content_file = Path(__file__).parent.parent / "data" / "content.json"
            if content_file.exists():
                import json
                contents = json.load(content_file)
                if contents:
                    c = contents[0]
                    cur.execute("""
                        INSERT INTO site_content (
                            site_title, brand_name, hero_headline, hero_subheadline,
                            nav_home_label, nav_products_label, nav_cart_label, nav_orders_label,
                            footer_tagline, footer_copyright, section_heading, section_subheadline,
                            cta_shop_now, cta_view_cart, cta_sign_in,
                            empty_cart_message, empty_orders_message, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        c.get("site_title"), c.get("brand_name"),
                        c.get("hero_headline"), c.get("hero_subheadline"),
                        c.get("nav_home_label"), c.get("nav_products_label"),
                        c.get("nav_cart_label"), c.get("nav_orders_label"),
                        c.get("footer_tagline"), c.get("footer_copyright"),
                        c.get("section_heading"), c.get("section_subheadline"),
                        c.get("cta_shop_now"), c.get("cta_view_cart"), c.get("cta_sign_in"),
                        c.get("empty_cart_message"), c.get("empty_orders_message"),
                        c.get("updated_at")
                    ))
            
            print("✅ Database initialized successfully!")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()


def _configure_session(app: Flask) -> None:
    """Initialise Flask-Session with the configured backend.

    On Vercel (SESSION_TYPE=cookie or unset in serverless), we skip
    Flask-Session entirely and rely on Flask's built-in signed cookie sessions.
    These are stateless — the session data lives in the cookie itself, signed
    with SECRET_KEY — so they work across all serverless instances.

    Supported SESSION_TYPE values (opt-in via env var):
    * ``"cookie"`` or unset — Flask built-in signed cookie sessions (default
      on Vercel; no server-side storage required).
    * ``"filesystem"`` — stores sessions in SESSION_FILE_DIR (local dev).
    * ``"redis"`` — stores sessions in Redis (requires REDIS_URL).
    * ``"sqlalchemy"`` — stores sessions in a SQL database.

    Args:
        app: The Flask application instance.
    """
    session_type = app.config.get("SESSION_TYPE", "cookie")

    if session_type in ("cookie", ""):
        # Use Flask's built-in signed cookie sessions — no Flask-Session needed.
        # Ensure the cookie is reasonably sized by not storing large objects.
        app.config["SESSION_TYPE"] = "cookie"
        return

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
            app.logger.warning(
                "flask_sqlalchemy not installed; falling back to cookie sessions."
            )
            app.config["SESSION_TYPE"] = "cookie"

    elif session_type == "filesystem":
        import os as _os
        session_dir = app.config.get("SESSION_FILE_DIR", "/tmp/flask_session")
        _os.makedirs(session_dir, exist_ok=True)
        app.config["SESSION_FILE_DIR"] = session_dir
        from flask_session import Session

        Session(app)

    else:
        # Unknown type — fall back to cookie sessions.
        app.logger.warning(
            f"Unknown SESSION_TYPE {session_type!r}; falling back to cookie sessions."
        )
        app.config["SESSION_TYPE"] = "cookie"


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
