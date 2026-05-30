"""Vercel serverless entry point.

Vercel's Python runtime looks for an ``app`` (or ``handler``) object in
``api/index.py``.  We simply import the Flask application factory and
expose the configured app instance.
"""

import os
import sys

# Make the project root importable so that ``app``, ``config``, etc. resolve.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app("production")
