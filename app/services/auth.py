from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.db.database import get_connection

JWT_ALGORITHM = "HS256"


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def register_user(email: str, password: str) -> int:
    password_hash = _hash_password(password)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
            if cur.fetchone() is not None:
                raise ValueError("A user with this email already exists.")

            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id;",
                (email, password_hash),
            )
            user_id = cur.fetchone()[0]

    return user_id


def authenticate_user(email: str, password: str) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s;", (email,))
            row = cur.fetchone()

    # Same error whether the email doesn't exist or the password is wrong -
    # confirming "that email isn't registered" to a caller is its own
    # information leak.
    if row is None or not _verify_password(password, row[1]):
        raise ValueError("Invalid email or password.")

    return row[0]


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "type": "access", "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {"sub": str(user_id), "type": "refresh", "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def _decode(token: str, expected_type: str, error_message: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as e:
        raise ValueError(error_message) from e

    # A refresh token must never work as an access token and vice versa -
    # without this check, a long-lived refresh token leaked from storage
    # could be used directly against every endpoint, not just /auth/refresh.
    if payload.get("type") != expected_type:
        raise ValueError(error_message)

    return int(payload["sub"])


def decode_access_token(token: str) -> int:
    return _decode(token, "access", "Invalid or expired token.")


def decode_refresh_token(token: str) -> int:
    return _decode(token, "refresh", "Invalid or expired refresh token.")
