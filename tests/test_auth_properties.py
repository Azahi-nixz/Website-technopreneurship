"""Property-based tests for the authentication service and routes.

# Feature: commercial-ecommerce-website

Properties covered:
  Property 1: Password hashing uses bcrypt with cost factor >= 12
  Property 2: Registration with valid credentials creates a retrievable user
  Property 3: Duplicate email registration is rejected with 409
  Property 4: Login/logout session round-trip
  Property 5: Invalid credentials always return a generic 401
"""

import re
import sys
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import bcrypt
import pytest
from flask import Flask, session
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# psycopg2 is no longer used — the app uses a pure-Python UniqueViolation.
# The stub below is kept for backward compatibility with any remaining
# references in this test file.
# ---------------------------------------------------------------------------

if "psycopg2" not in sys.modules:
    _psycopg2_stub = types.ModuleType("psycopg2")
    _errors_stub = types.ModuleType("psycopg2.errors")

    class _UniqueViolation(Exception):
        """Stub for psycopg2.errors.UniqueViolation."""

    _errors_stub.UniqueViolation = _UniqueViolation
    _psycopg2_stub.errors = _errors_stub

    sys.modules["psycopg2"] = _psycopg2_stub
    sys.modules["psycopg2.errors"] = _errors_stub

# Also stub app.db so importing user_repository doesn't fail.
if "app.db" not in sys.modules:
    _db_stub = types.ModuleType("app.db")
    _db_stub.get_connection = MagicMock()
    sys.modules["app.db"] = _db_stub

from app.middleware.csrf import validate_csrf
from app.errors import register_error_handlers
from app.routes.auth_routes import auth_bp
from app.services.auth_service import hash_password, register, ConflictError

# ---------------------------------------------------------------------------
# Hypothesis settings
# ---------------------------------------------------------------------------

settings.register_profile("test_auth", max_examples=50)
settings.load_profile("test_auth")

# ---------------------------------------------------------------------------
# Custom Hypothesis strategies
# ---------------------------------------------------------------------------


def valid_email():
    """Generate syntactically valid email addresses."""
    local_part = st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu", "Nd"),
            whitelist_characters="-_.",
        ),
        min_size=1,
        max_size=20,
    ).filter(lambda s: s and not s.startswith(".") and not s.endswith("."))

    domain_label = st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu", "Nd"),
            whitelist_characters="-",
        ),
        min_size=1,
        max_size=15,
    ).filter(lambda s: s and not s.startswith("-") and not s.endswith("-"))

    tld = st.sampled_from(["com", "net", "org", "io", "co"])

    return st.builds(
        lambda local, domain, tld_: f"{local}@{domain}.{tld_}",
        local_part,
        domain_label,
        tld,
    )


# ---------------------------------------------------------------------------
# Flask test application factory
# ---------------------------------------------------------------------------


def _make_test_app():
    """Create a minimal Flask app for testing auth routes.

    Uses a filesystem-backed session (cookie-based) so no DB is needed for
    session storage.  CSRF validation is registered but tests that need to
    call state-changing endpoints must supply the token explicitly.
    """
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key-for-hypothesis",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        WTF_CSRF_ENABLED=False,
    )
    app.register_blueprint(auth_bp)
    register_error_handlers(app)
    # Do NOT register CSRF middleware for unit-level property tests — the
    # register and login endpoints are exempt anyway, and logout/me tests
    # manage the CSRF token explicitly via the helper below.
    return app


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_user(email: str, password: str):
    """Return a mock User object with a real bcrypt hash."""
    from app.models.user import User

    hashed = hash_password(password).decode("utf-8")
    return User(
        id=uuid4(),
        email=email,
        password_hash=hashed,
        created_at=datetime.now(timezone.utc),
    )


def _csrf_token_for(client):
    """Fetch a CSRF token from the test client's session."""
    resp = client.get("/api/v1/csrf-token")
    return resp.get_json()["csrf_token"]


# ---------------------------------------------------------------------------
# Property 1: Password hashing uses bcrypt with cost factor >= 12
# ---------------------------------------------------------------------------


@given(st.text(min_size=1))
@settings(max_examples=50)
def test_hash_password_cost_factor_at_least_12(password):
    """Property 1: Password hashing uses bcrypt with cost factor >= 12.

    # Feature: commercial-ecommerce-website, Property 1: Password hashing uses bcrypt with cost factor >= 12

    **Validates: Requirements 1.1**

    For any non-empty password string, hash_password() must produce a bcrypt
    hash whose embedded cost factor is >= 12.  The cost factor is encoded in
    the hash string as the numeric field between the second and third '$'
    separators, e.g. '$2b$12$...'.
    """
    hashed = hash_password(password)

    # hash_password returns bytes; decode to inspect the prefix.
    assert isinstance(hashed, bytes), "hash_password must return bytes"

    hash_str = hashed.decode("utf-8")

    # bcrypt hash format: $<version>$<cost>$<salt+digest>
    # e.g. $2b$12$...
    match = re.match(r"^\$2[ab]?\$(\d+)\$", hash_str)
    assert match is not None, (
        f"hash_password({password!r}) returned a string that does not look "
        f"like a valid bcrypt hash: {hash_str!r}"
    )

    cost_factor = int(match.group(1))
    assert cost_factor >= 12, (
        f"hash_password({password!r}) used cost factor {cost_factor}, "
        f"expected >= 12"
    )

    # Also verify the hash round-trips correctly.
    assert bcrypt.checkpw(password.encode("utf-8"), hashed), (
        f"bcrypt.checkpw failed for password {password!r}"
    )


# ---------------------------------------------------------------------------
# Property 2: Registration with valid credentials creates a retrievable user
# ---------------------------------------------------------------------------


@given(valid_email(), st.text(min_size=8))
@settings(max_examples=50)
def test_registration_creates_retrievable_user(email, password):
    """Property 2: Registration with valid credentials creates a retrievable user.

    # Feature: commercial-ecommerce-website, Property 2: Registration with valid credentials creates a retrievable user

    **Validates: Requirements 1.2**

    For any syntactically valid email and password of length >= 8, calling
    register() must create a user whose stored password hash verifies against
    the original password.
    """
    expected_user = _make_user(email, password)

    with patch("app.services.auth_service.user_repository") as mock_repo:
        mock_repo.create_user.return_value = expected_user
        mock_repo.find_by_email.return_value = expected_user

        # Call register — should not raise.
        created_user = register(email, password)

        # Verify create_user was called with the email and a non-empty hash.
        mock_repo.create_user.assert_called_once()
        call_args = mock_repo.create_user.call_args
        stored_email = call_args[0][0]
        stored_hash = call_args[0][1]

        assert stored_email == email, (
            f"register() stored email {stored_email!r}, expected {email!r}"
        )
        assert stored_hash, "register() must store a non-empty password hash"

        # The stored hash must verify against the original password.
        assert bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")), (
            f"Stored hash for {email!r} does not verify against the original password"
        )

        # The returned user must have the correct email.
        assert created_user.email == email, (
            f"register() returned user with email {created_user.email!r}, "
            f"expected {email!r}"
        )


# ---------------------------------------------------------------------------
# Property 3: Duplicate email registration is rejected with 409
# ---------------------------------------------------------------------------


@given(valid_email(), st.text(min_size=8))
@settings(max_examples=50)
def test_duplicate_email_registration_returns_409(email, password):
    """Property 3: Duplicate email registration is rejected with 409.

    # Feature: commercial-ecommerce-website, Property 3: Duplicate email registration is rejected with 409

    **Validates: Requirements 1.3**

    For any email that has already been registered, a second registration
    attempt with the same email must return HTTP 409 Conflict.
    """
    import psycopg2.errors

    app = _make_test_app()

    with app.test_client() as client:
        # First registration: succeed.
        first_user = _make_user(email, password)
        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.create_user.return_value = first_user

            resp1 = client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password},
            )
            assert resp1.status_code == 201, (
                f"First registration for {email!r} returned {resp1.status_code}, "
                f"expected 201. Body: {resp1.get_json()}"
            )

        # Second registration: simulate UniqueViolation from the DB.
        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.create_user.side_effect = psycopg2.errors.UniqueViolation(
                "duplicate key value violates unique constraint"
            )

            resp2 = client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password},
            )
            assert resp2.status_code == 409, (
                f"Duplicate registration for {email!r} returned {resp2.status_code}, "
                f"expected 409. Body: {resp2.get_json()}"
            )

            body = resp2.get_json()
            assert "error" in body, "409 response must contain an 'error' key"
            assert body["error"]["code"] == "EMAIL_CONFLICT", (
                f"Expected error code 'EMAIL_CONFLICT', got {body['error']['code']!r}"
            )


# ---------------------------------------------------------------------------
# Property 4: Login/logout session round-trip
# ---------------------------------------------------------------------------


@given(valid_email(), st.text(min_size=8))
@settings(max_examples=50)
def test_login_logout_session_round_trip(email, password):
    """Property 4: Login/logout session round-trip.

    # Feature: commercial-ecommerce-website, Property 4: Login/logout session round-trip

    **Validates: Requirements 1.4, 1.6**

    For any registered user, logging in with correct credentials must create a
    valid session (GET /me returns 200), and after logout that session must be
    invalid (GET /me returns 401).
    """
    app = _make_test_app()
    # Register CSRF middleware so logout (POST) requires a token.
    validate_csrf(app)

    user = _make_user(email, password)

    with app.test_client() as client:
        # --- Login ---
        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.find_by_email.return_value = user

            login_resp = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            assert login_resp.status_code == 200, (
                f"Login for {email!r} returned {login_resp.status_code}, "
                f"expected 200. Body: {login_resp.get_json()}"
            )

        # --- Session valid: GET /me should return 200 ---
        with patch("app.services.auth_service.user_repository") as mock_repo:
            mock_repo.find_by_id.return_value = user

            me_resp = client.get("/api/v1/auth/me")
            assert me_resp.status_code == 200, (
                f"GET /me after login returned {me_resp.status_code}, "
                f"expected 200. Body: {me_resp.get_json()}"
            )

        # --- Logout ---
        # Fetch CSRF token first (GET is exempt from CSRF).
        csrf_resp = client.get("/api/v1/csrf-token")
        csrf_token = csrf_resp.get_json()["csrf_token"]

        logout_resp = client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        assert logout_resp.status_code == 200, (
            f"Logout for {email!r} returned {logout_resp.status_code}, "
            f"expected 200. Body: {logout_resp.get_json()}"
        )

        # --- Session invalid: GET /me should return 401 ---
        me_after_logout = client.get("/api/v1/auth/me")
        assert me_after_logout.status_code == 401, (
            f"GET /me after logout returned {me_after_logout.status_code}, "
            f"expected 401. Body: {me_after_logout.get_json()}"
        )


# ---------------------------------------------------------------------------
# Property 5: Invalid credentials always return a generic 401
# ---------------------------------------------------------------------------


def _invalid_credentials():
    """Generate (email, password) pairs where credentials are invalid.

    Two cases:
      a) Email is not registered (unknown email, any password).
      b) Email is registered but password does not match.
    """
    # Case (a): unregistered email
    unregistered = st.tuples(valid_email(), st.text(min_size=1)).map(
        lambda t: ("unregistered", t[0], t[1])
    )
    # Case (b): registered email, wrong password
    wrong_password = st.tuples(
        valid_email(),
        st.text(min_size=8),   # correct password (used to create user)
        st.text(min_size=1),   # wrong password (different from correct)
    ).filter(lambda t: t[1] != t[2]).map(
        lambda t: ("wrong_password", t[0], t[2])
    )
    return st.one_of(unregistered, wrong_password)


@given(_invalid_credentials())
@settings(max_examples=50)
def test_invalid_credentials_return_generic_401(cred_tuple):
    """Property 5: Invalid credentials always return a generic 401.

    # Feature: commercial-ecommerce-website, Property 5: Invalid credentials always return a generic 401

    **Validates: Requirements 1.5**

    For any (email, password) pair where either the email is not registered or
    the password does not match, the login endpoint must return 401 and the
    response body must NOT disclose which field (email or password) was wrong.
    """
    case, email, password = cred_tuple

    app = _make_test_app()

    with app.test_client() as client:
        if case == "unregistered":
            # Email not in DB → find_by_email returns None.
            with patch("app.services.auth_service.user_repository") as mock_repo:
                mock_repo.find_by_email.return_value = None

                resp = client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                )
        else:
            # Registered email but wrong password.
            correct_password = email + "_correct_pw_123"  # guaranteed != password
            user = _make_user(email, correct_password)

            with patch("app.services.auth_service.user_repository") as mock_repo:
                mock_repo.find_by_email.return_value = user

                resp = client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                )

        assert resp.status_code == 401, (
            f"Login with invalid credentials ({case}) returned {resp.status_code}, "
            f"expected 401. Body: {resp.get_json()}"
        )

        body = resp.get_json()
        assert body is not None, "401 response must have a JSON body"

        # The response must not disclose which field was wrong.
        body_str = str(body).lower()
        assert "email" not in body_str or "invalid" in body_str, (
            "401 response must not specifically mention 'email' as the failing field"
        )
        # The generic message must be present.
        error_section = body.get("error", body)
        message = error_section.get("message", "")
        assert message, "401 response must include a non-empty message"

        # Verify the message is the same generic string regardless of which
        # field was wrong — it must not say "email not found" vs "wrong password".
        assert "invalid credentials" in message.lower() or "unauthorized" in message.lower(), (
            f"401 message {message!r} should be a generic 'invalid credentials' "
            f"message, not field-specific"
        )
