"""Application configuration classes.

Provides ``DevelopmentConfig`` and ``ProductionConfig`` that read settings
from environment variables.  Pass the config name string (``"development"``
or ``"production"``) to :func:`app.create_app` to select the appropriate
class.

Requirements: 9.1, 9.5, 11.1, 11.2
"""

import os


class BaseConfig:
    """Shared defaults for all environments."""

    # Flask core
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
    TESTING: bool = False

    # Flask built-in signed cookie session
    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_HTTPONLY: bool = True
    # "Lax" allows the session cookie on top-level GET navigations (post-login
    # redirects).  "Strict" would drop the cookie on every redirect, logging
    # the user out immediately after a successful login.
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # Flask-Session (only used when SESSION_TYPE != "cookie")
    SESSION_TYPE: str = os.environ.get("SESSION_TYPE", "filesystem")
    SESSION_FILE_DIR: str = os.environ.get("SESSION_FILE_DIR", "/tmp/flask_session")
    SESSION_PERMANENT: bool = False
    SESSION_USE_SIGNER: bool = True

    # Redis (optional — only used when SESSION_TYPE=redis)
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Database
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # SQLAlchemy (used by Flask-Session when SESSION_TYPE=sqlalchemy)
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///sessions.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False


class DevelopmentConfig(BaseConfig):
    """Configuration for local development.

    * DEBUG is enabled so Flask reloads on code changes and shows the
      interactive debugger.
    * Session cookies are *not* marked Secure so they work over plain HTTP.
    * Defaults to filesystem-based sessions so no database is required just
      to start the dev server.
    """

    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False


class ProductionConfig(BaseConfig):
    """Configuration for production deployments.

    * DEBUG is disabled.
    * Session cookies are marked Secure, enforcing HTTPS (Requirement 11.1).
    * SESSION_TYPE defaults to ``"cookie"`` — Flask's built-in signed cookie
      sessions, which are stateless and work on serverless platforms like
      Vercel without any external storage.  Override via SESSION_TYPE env var
      if you have Redis or a database available.
    """

    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True
    SESSION_TYPE: str = os.environ.get("SESSION_TYPE", "cookie")


# Mapping from string name → config class, used by create_app().
_CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config(name: str = None):
    """Return the config class for the given environment name.

    Falls back to the ``FLASK_ENV`` environment variable, then to
    ``DevelopmentConfig`` if neither is provided.

    Args:
        name: ``"development"`` or ``"production"``.  Case-insensitive.

    Returns:
        A config class (not an instance).

    Raises:
        ValueError: if *name* is not a recognised environment name.
    """
    if name is None:
        name = os.environ.get("FLASK_ENV", "development")

    key = name.lower()
    if key not in _CONFIG_MAP:
        raise ValueError(
            f"Unknown config name {name!r}. "
            f"Valid options are: {', '.join(_CONFIG_MAP)}"
        )
    return _CONFIG_MAP[key]
