"""Vercel serverless entry point.

Vercel's Python runtime looks for an ``app`` (or ``handler``) object in
``api/index.py``.  We import the Flask application factory and expose the
configured app instance.
"""

import os
import sys

# Ensure the project root (parent of this file's directory) is on sys.path
# so that ``app``, ``config``, etc. are importable.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dotenv import load_dotenv

# Load .env if present (no-op in production where env vars are set directly).
load_dotenv(os.path.join(_root, ".env"))

from app import create_app  # noqa: E402

app = create_app("production")
