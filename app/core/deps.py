from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth import decode_access_token

bearer_scheme = HTTPBearer(description="JWT access token from POST /auth/login or /auth/register")


def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """Validate the bearer token and return the user id.

    Deliberately does NOT call set_current_user_id() here: FastAPI runs a
    sync dependency like this one in its own threadpool dispatch, which
    copies the contextvars context for that call only. A ContextVar.set()
    made inside that copy never reaches the (separately dispatched) sync
    endpoint function - each route must call set_current_user_id(user_id)
    itself, as the first thing it does, so the set happens in the same
    context the rest of the request actually runs in.
    """
    try:
        return decode_access_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
