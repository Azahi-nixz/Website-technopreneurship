"""Auth service — business logic for registration, login, and user lookup.

Session management (creating/invalidating sessions) is handled by Flask-Session
in the routes layer.  This service handles only credential verification.

Security notes:
- Passwords are hashed with bcrypt at cost factor 12 (Requirement 1.1).
- Login errors return a single generic message regardless of whether the email
  or the password was wrong, preventing field-level disclosure (Requirement 1.5).
"""

from typing import Optional
from uuid import UUID

import bcrypt

from app.models.user import User
from app.repositories import user_repository  # noqa: E402 — must come after shim setup

# Import user_repository first so its module-level shim patches psycopg2.errors
import psycopg2.errors  # noqa: E402


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class ConflictError(Exception):
    """Raised when a resource conflict is detected (e.g. duplicate email)."""


class AuthError(Exception):
    """Raised when authentication fails (invalid credentials)."""


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> bytes:
    """Hash *password* with bcrypt at cost factor 12.

    Args:
        password: The plain-text password to hash.

    Returns:
        The bcrypt hash as bytes.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))


def verify_password(password: str, password_hash: str) -> bool:
    """Check whether *password* matches *password_hash*.

    Args:
        password: The plain-text password to verify.
        password_hash: A bcrypt hash (str or bytes) to check against.

    Returns:
        True if the password matches, False otherwise.
    """
    if isinstance(password_hash, str):
        password_hash = password_hash.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), password_hash)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

def register(email: str, password: str) -> User:
    """Register a new user with the given *email* and *password*.

    Hashes the password with bcrypt before persisting it.

    Args:
        email: The user's email address (must be unique).
        password: The plain-text password chosen by the user.

    Returns:
        The newly created User instance.

    Raises:
        ConflictError: If the email address is already registered.
    """
    hashed = hash_password(password)
    # Store the hash as a UTF-8 string so it fits the VARCHAR column.
    hashed_str = hashed.decode("utf-8")
    try:
        return user_repository.create_user(email, hashed_str)
    except psycopg2.errors.UniqueViolation:
        raise ConflictError("Email already registered.")


def login(email: str, password: str) -> User:
    """Authenticate a user by email and password.

    Returns the User on success.  Raises AuthError with a generic message on
    failure — the same message is used whether the email is unknown or the
    password is wrong, to avoid disclosing which field was incorrect
    (Requirement 1.5).

    Args:
        email: The email address supplied by the user.
        password: The plain-text password supplied by the user.

    Returns:
        The authenticated User instance.

    Raises:
        AuthError: If the email is not found or the password does not match.
    """
    user = user_repository.find_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Invalid credentials.")
    return user


def get_current_user(user_id: str) -> Optional[User]:
    """Return the User identified by *user_id*, or None if not found.

    Args:
        user_id: A string representation of the user's UUID primary key,
                 typically read from the server-side session.

    Returns:
        The User instance if found, otherwise None.
    """
    return user_repository.find_by_id(UUID(user_id))
