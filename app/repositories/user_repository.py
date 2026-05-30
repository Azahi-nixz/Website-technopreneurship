"""User repository — JSON file-based storage for users."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.db import read_collection, write_collection
from app.models.user import User

_COL = "users"


def _row_to_user(d: dict) -> User:
    return User(
        id=UUID(d["id"]),
        email=d["email"],
        password_hash=d["password_hash"],
        created_at=datetime.fromisoformat(d["created_at"]),
        is_admin=bool(d.get("is_admin", False)),
    )


class UniqueViolation(Exception):
    """Raised when a duplicate email is detected (mirrors psycopg2 behaviour)."""


def create_user(email: str, password_hash: str, is_admin: bool = False) -> User:
    users = read_collection(_COL)
    # Enforce uniqueness
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
    write_collection(_COL, users)
    return _row_to_user(user)


def find_by_email(email: str) -> Optional[User]:
    users = read_collection(_COL)
    for u in users:
        if u["email"].lower() == email.lower():
            return _row_to_user(u)
    return None


def find_by_id(user_id: UUID) -> Optional[User]:
    users = read_collection(_COL)
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
    users = read_collection(_COL)
    for u in users:
        if u["email"].lower() == email.lower():
            u["is_admin"] = is_admin
            break
    write_collection(_COL, users)
