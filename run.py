"""Application entry point.

Run the development server with::

    python run.py

Or use the Flask CLI::

    flask --app run:app run

In production, point a WSGI server (gunicorn, uWSGI, etc.) at the ``app``
object exported from this module::

    gunicorn "run:app"

Requirements: 9.1, 11.1
"""

import os

from dotenv import load_dotenv

# Load .env before importing the app so that environment variables are
# available when config.py reads them.
load_dotenv()

from app import create_app  # noqa: E402 — must come after load_dotenv()

# Determine the environment from FLASK_ENV (defaults to "development").
_env = os.environ.get("FLASK_ENV", "development")

app = create_app(_env)

if __name__ == "__main__":
    debug = app.config.get("DEBUG", False)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug)
