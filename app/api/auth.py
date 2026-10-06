from fastapi import APIRouter, HTTPException

from app.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens(user_id: int) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register a new user",
    description="Creates a new user and returns an access + refresh token, same as /auth/login would.",
)
def register(request: RegisterRequest) -> TokenResponse:
    try:
        user_id = register_user(request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return _tokens(user_id)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and get an access + refresh token",
    description="Exchanges an email/password for a JWT access token (use as a Bearer token) and a longer-lived refresh token.",
)
def login(request: LoginRequest) -> TokenResponse:
    try:
        user_id = authenticate_user(request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return _tokens(user_id)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new access token",
    description=(
        "Issues a new access token from a still-valid refresh token, so a client doesn't "
        "need to re-enter a password every time the (short-lived) access token expires. "
        "The refresh token itself is returned unchanged - there's no server-side store to "
        "rotate or revoke it against, so a compromised refresh token stays valid until it "
        "naturally expires."
    ),
)
def refresh(request: RefreshRequest) -> TokenResponse:
    try:
        user_id = decode_refresh_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=request.refresh_token,
    )
