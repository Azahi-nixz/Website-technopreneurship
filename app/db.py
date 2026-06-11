"""PostgreSQL database connection for Vercel Postgres.

Provides a connection pool and helper to get database connections.
Falls back to JSON files when POSTGRES_URL is not set (local dev).
"""

import os
from contextlib import contextmanager

# Check if we have a PostgreSQL URL
POSTGRES_URL = os.environ.get("POSTGRES_URL", "")
USE_POSTGRES = bool(POSTGRES_URL)

if USE_POSTGRES:
    import pg8000.native
    from urllib.parse import urlparse
    
    # Parse the POSTGRES_URL
    parsed = urlparse(POSTGRES_URL)
    
    _db_params = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path[1:],  # Remove leading /
        "user": parsed.username,
        "password": parsed.password,
        "ssl_context": True,  # Enable SSL
    }
    
    @contextmanager
    def get_connection():
        """Get a database connection."""
        conn = pg8000.native.Connection(**_db_params)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # Define a UniqueViolation exception that matches psycopg2's behavior
    class UniqueViolation(Exception):
        """Raised when a unique constraint is violated."""

else:
    # Fallback to JSON files for local development
    import json
    import shutil
    from pathlib import Path
    from threading import Lock

    _SEED_DIR = Path(__file__).resolve().parent.parent / "data"
    _DATA_DIR = None
    _LOCKS = {}

    def _get_data_dir():
        global _DATA_DIR
        if _DATA_DIR is not None:
            return _DATA_DIR

        test_path = _SEED_DIR / ".write_test"
        try:
            _SEED_DIR.mkdir(exist_ok=True)
            test_path.touch()
            test_path.unlink()
            _DATA_DIR = _SEED_DIR
            return _DATA_DIR
        except OSError:
            pass

        tmp_dir = Path("/tmp/data")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        if _SEED_DIR.exists():
            for seed_file in _SEED_DIR.glob("*.json"):
                dest = tmp_dir / seed_file.name
                if not dest.exists():
                    try:
                        shutil.copy2(seed_file, dest)
                    except OSError:
                        pass
        _DATA_DIR = tmp_dir
        return _DATA_DIR

    def _lock_for(name):
        if name not in _LOCKS:
            _LOCKS[name] = Lock()
        return _LOCKS[name]

    def _path(name):
        return _get_data_dir() / f"{name}.json"

    def read_collection(name):
        p = _path(name)
        if not p.exists():
            seed = _SEED_DIR / f"{name}.json"
            if seed.exists():
                with open(seed, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []
        with _lock_for(name):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

    def write_collection(name, data):
        p = _path(name)
        try:
            with _lock_for(name):
                tmp = p.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                tmp.replace(p)
        except OSError:
            pass
    
    @contextmanager
    def get_connection():
        """Dummy context manager for JSON file backend (no connection needed)."""
        yield None
