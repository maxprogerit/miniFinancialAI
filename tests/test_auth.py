"""Auth service unit tests: register/login edge cases, JWT validation.

Requires the dev stack running (needs the real users table + demo1 seed
user). Registration tests create a throwaway user and delete it afterward.
"""
import time
import uuid

import jwt
import pytest

from app.core.config import settings
from app.db.database import get_connection
from app.services.auth import (
    JWT_ALGORITHM,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    register_user,
)


@pytest.fixture
def temp_email():
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    yield email
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))


def test_register_and_login_roundtrip(temp_email):
    user_id = register_user(temp_email, "SomePassword123!")
    assert isinstance(user_id, int)
    assert authenticate_user(temp_email, "SomePassword123!") == user_id


def test_register_duplicate_email_rejected(temp_email):
    register_user(temp_email, "SomePassword123!")
    with pytest.raises(ValueError, match="already exists"):
        register_user(temp_email, "AnotherPassword123!")


def test_login_wrong_password_rejected():
    with pytest.raises(ValueError, match="Invalid email or password"):
        authenticate_user("demo1@example.com", "wrong-password")


def test_login_unknown_email_rejected_with_same_message_as_wrong_password():
    # Deliberately indistinguishable from a wrong password - confirming an
    # email is/isn't registered is its own information leak.
    with pytest.raises(ValueError, match="Invalid email or password"):
        authenticate_user("nobody-here@example.com", "whatever")


def test_access_token_roundtrip():
    token = create_access_token(123)
    assert decode_access_token(token) == 123


def test_expired_token_rejected():
    expired_payload = {"sub": "1", "exp": time.time() - 10}
    token = jwt.encode(expired_payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_access_token(token)


def test_tampered_token_rejected():
    token = create_access_token(1)
    with pytest.raises(ValueError):
        decode_access_token(token + "x")


def test_refresh_token_roundtrip():
    token = create_refresh_token(123)
    assert decode_refresh_token(token) == 123


def test_access_token_rejected_as_refresh_token():
    # A leaked access token must not double as a refresh token - it carries
    # type=access, so decode_refresh_token must reject it outright.
    token = create_access_token(1)
    with pytest.raises(ValueError, match="Invalid or expired refresh token"):
        decode_refresh_token(token)


def test_refresh_token_rejected_as_access_token():
    # And the reverse: a refresh token must not work directly against
    # endpoints that expect an access token.
    token = create_refresh_token(1)
    with pytest.raises(ValueError, match="Invalid or expired token"):
        decode_access_token(token)
