from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth import decode_access_token

bearer_scheme = HTTPBearer(description="JWT access token from POST /auth/login or /auth/register")


def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """Validate the bearer token and return the user id.

    Routes call set_current_user_id() themselves: a ContextVar set in a sync dependency does not reach the route.
    """
    try:
        return decode_access_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
