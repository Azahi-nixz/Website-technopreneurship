"""User repository — PostgreSQL storage for users."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.db import USE_POSTGRES, get_connection
from app.models.user import User

if USE_POSTGRES:
    from app.db import UniqueViolation
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
            user_id = uuid4()
            created_at = datetime.now(timezone.utc)
            try:
                result = conn.run("""
                    INSERT INTO users (id, email, password_hash, created_at, is_admin)
                    VALUES (:id, :email, :password_hash, :created_at, :is_admin)
                    RETURNING id, email, password_hash, created_at, is_admin
                """, id=str(user_id), email=email, password_hash=password_hash, 
                   created_at=created_at, is_admin=is_admin)
                return _row_to_user(result[0])
            except Exception as e:
                if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                    raise UniqueViolation(f"Email {email!r} already registered.")
                raise
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
            result = conn.run("""
                SELECT id, email, password_hash, created_at, is_admin
                FROM users WHERE LOWER(email) = LOWER(:email)
            """, email=email)
            return _row_to_user(result[0]) if result else None
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
            result = conn.run("""
                SELECT id, email, password_hash, created_at, is_admin
                FROM users WHERE id = :id
            """, id=str(user_id))
            return _row_to_user(result[0]) if result else None
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
            conn.run("""
                UPDATE users SET is_admin = :is_admin WHERE LOWER(email) = LOWER(:email)
            """, is_admin=is_admin, email=email)
    else:
        from app.db import read_collection, write_collection
        users = read_collection("users")
        for u in users:
            if u["email"].lower() == email.lower():
                u["is_admin"] = is_admin
                break
        write_collection("users", users)
