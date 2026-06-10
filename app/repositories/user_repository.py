"""User repository — PostgreSQL storage for users."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.db import USE_POSTGRES, get_connection
from app.models.user import User

if USE_POSTGRES:
    import psycopg2.errors
    UniqueViolation = psycopg2.errors.UniqueViolation
else:
    class UniqueViolation(Exception):
        """Raised when a duplicate email is detected."""


def _row_to_user(row) -> User:
    """Convert database row or dict to User model."""
    if isinstance(row, dict):
        return User(
            id=UUID(row["id"]),
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=datetime.fromisoformat(row["created_at"]),
            is_admin=bool(row.get("is_admin", False)),
        )
    else:
        # PostgreSQL row tuple: (id, email, password_hash, created_at, is_admin)
        return User(
            id=UUID(row[0]),
            email=row[1],
            password_hash=row[2],
            created_at=row[3],
            is_admin=bool(row[4]) if len(row) > 4 else False,
        )


def create_user(email: str, password_hash: str, is_admin: bool = False) -> User:
    """Create a new user."""
    if USE_POSTGRES:
        with get_connection() as conn:
            cur = conn.cursor()
            user_id = uuid4()
            created_at = datetime.now(timezone.utc)
            try:
                cur.execute("""
                    INSERT INTO users (id, email, password_hash, created_at, is_admin)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, email, password_hash, created_at, is_admin
                """, (str(user_id), email, password_hash, created_at, is_admin))
                row = cur.fetchone()
                return _row_to_user(row)
            except psycopg2.errors.UniqueViolation:
                raise UniqueViolation(f"Email {email!r} already registered.")
    else:
        # JSON fallback
        from app.db import read_collection, write_collection
        users = read_collection("users")
        if any(u["email"].lower() == email.lower() for u in users):
            raise UniqueViolation(f"Email {email!r} already registered.")
        user = {
            "id": str(uuid4()),
            "email": email,
            "password_hash": password_hash,
            "is_admin": is_admin,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        users.append(user)
        write_collection("users", users)
        return _row_to_user(user)


def find_by_email(email: str) -> Optional[User]:
    """Find user by email (case-insensitive)."""
    if USE_POSTGRES:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, email, password_hash, created_at, is_admin
                FROM users WHERE LOWER(email) = LOWER(%s)
            """, (email,))
            row = cur.fetchone()
            return _row_to_user(row) if row else None
    else:
        from app.db import read_collection
        users = read_collection("users")
        for u in users:
            if u["email"].lower() == email.lower():
                return _row_to_user(u)
        return None


def find_by_id(user_id: UUID) -> Optional[User]:
    """Find user by ID."""
    if USE_POSTGRES:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, email, password_hash, created_at, is_admin
                FROM users WHERE id = %s
            """, (str(user_id),))
            row = cur.fetchone()
            return _row_to_user(row) if row else None
    else:
        from app.db import read_collection
        users = read_collection("users")
        sid = str(user_id)
        for u in users:
            if u["id"] == sid:
                return _row_to_user(u)
        return None


def find_admin_by_email(email: str) -> Optional[User]:
    """Return the user with the given email only if they are an admin."""
    user = find_by_email(email)
    if user and user.is_admin:
        return user
    return None


def set_admin_flag(email: str, is_admin: bool) -> None:
    """Set the is_admin flag for the user with the given email."""
    if USE_POSTGRES:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE users SET is_admin = %s WHERE LOWER(email) = LOWER(%s)
            """, (is_admin, email))
    else:
        from app.db import read_collection, write_collection
        users = read_collection("users")
        for u in users:
            if u["email"].lower() == email.lower():
                u["is_admin"] = is_admin
                break
        write_collection("users", users)
