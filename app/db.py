"""JSON file-based data store.

Replaces the PostgreSQL backend with simple JSON files stored in the
``data/`` directory at the project root.  Suitable for local-only use.

Files:
  data/users.json       — list of user objects
  data/products.json    — list of product objects (with embedded images)
  data/cart_items.json  — list of cart item objects
  data/orders.json      — list of order objects (with embedded items)
"""

import json
import os
from pathlib import Path
from threading import Lock

# ---------------------------------------------------------------------------
# Storage directory
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_DIR.mkdir(exist_ok=True)

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
        return []
    with _lock_for(name):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)


def write_collection(name: str, data: list) -> None:
    """Atomically write *data* (a list) to ``data/<name>.json``."""
    p = _path(name)
    with _lock_for(name):
        tmp = p.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        tmp.replace(p)
