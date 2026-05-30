"""JSON file-based data store.

Stores data in JSON files.  On local development the files live in the
``data/`` directory at the project root.  On read-only serverless platforms
(e.g. Vercel) the ``data/`` directory is not writable, so the store
automatically copies the seed files to ``/tmp/data/`` on first access and
reads/writes from there for the lifetime of the process.

Files:
  data/users.json       — list of user objects
  data/products.json    — list of product objects (with embedded images)
  data/cart_items.json  — list of cart item objects
  data/orders.json      — list of order objects (with embedded items)
  data/theme.json       — site theme configuration
  data/content.json     — site content configuration
"""

import json
import os
import shutil
from pathlib import Path
from threading import Lock

# ---------------------------------------------------------------------------
# Storage directory resolution
# ---------------------------------------------------------------------------

# The canonical seed data lives next to this file's parent (project root).
_SEED_DIR = Path(__file__).resolve().parent.parent / "data"

# Determine the writable data directory.
# If the seed directory is writable we use it directly (local dev).
# Otherwise (Vercel / read-only FS) we shadow it under /tmp.
def _resolve_data_dir() -> Path:
    test_path = _SEED_DIR / ".write_test"
    try:
        _SEED_DIR.mkdir(exist_ok=True)
        test_path.touch()
        test_path.unlink()
        return _SEED_DIR
    except OSError:
        # Read-only filesystem — use /tmp shadow copy
        tmp_dir = Path("/tmp/data")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        # Copy any seed files that don't already exist in /tmp
        if _SEED_DIR.exists():
            for seed_file in _SEED_DIR.glob("*.json"):
                dest = tmp_dir / seed_file.name
                if not dest.exists():
                    shutil.copy2(seed_file, dest)
        return tmp_dir


_DATA_DIR: Path = _resolve_data_dir()

_LOCKS: dict[str, Lock] = {}


def _lock_for(name: str) -> Lock:
    if name not in _LOCKS:
        _LOCKS[name] = Lock()
    return _LOCKS[name]


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _path(name: str) -> Path:
    return _DATA_DIR / f"{name}.json"


def read_collection(name: str) -> list:
    """Read and return the JSON list stored in ``data/<name>.json``.

    Returns an empty list if the file does not exist yet.
    """
    p = _path(name)
    if not p.exists():
        # Fall back to seed directory if available
        seed = _SEED_DIR / f"{name}.json"
        if seed.exists():
            with open(seed, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    with _lock_for(name):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)


def write_collection(name: str, data: list) -> None:
    """Atomically write *data* (a list) to ``data/<name>.json``.

    On read-only filesystems this is a no-op (data persists only for the
    lifetime of the serverless process / warm instance).
    """
    p = _path(name)
    try:
        with _lock_for(name):
            tmp = p.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            tmp.replace(p)
    except OSError:
        # Silently ignore write failures on read-only filesystems.
        pass
