#!/usr/bin/env python3
"""Apply the initial database migration.

Usage::

    python scripts/init_db.py

The script reads the DATABASE_URL environment variable (or the individual
DB_* variables understood by ``app.db.get_connection``) and executes
``migrations/001_initial_schema.sql`` against the target database.

Set the environment variables before running, e.g.::

    export DATABASE_URL=postgresql://user:pass@localhost:5432/ecommerce
    python scripts/init_db.py
"""

import os
import sys
from pathlib import Path

# Allow importing app.db when running from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_connection  # noqa: E402  (import after sys.path tweak)

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
INITIAL_SCHEMA = MIGRATIONS_DIR / "001_initial_schema.sql"


def main() -> None:
    sql = INITIAL_SCHEMA.read_text(encoding="utf-8")

    print(f"Connecting to database …")
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        print("Migration applied successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
