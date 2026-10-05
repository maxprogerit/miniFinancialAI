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
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as e:
        raise ValueError("Invalid or expired token.") from e

    return int(payload["sub"])
