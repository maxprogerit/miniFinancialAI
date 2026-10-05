from fastapi import APIRouter, HTTPException

from app.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth import authenticate_user, create_access_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register a new user",
    description="Creates a new user and returns an access token, same as /auth/login would.",
)
def register(request: RegisterRequest) -> TokenResponse:
    try:
        user_id = register_user(request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TokenResponse(access_token=create_access_token(user_id))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in and get an access token",
    description="Exchanges an email/password for a JWT access token to use as a Bearer token on other endpoints.",
)
def login(request: LoginRequest) -> TokenResponse:
    try:
        user_id = authenticate_user(request.email, request.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return TokenResponse(access_token=create_access_token(user_id))
