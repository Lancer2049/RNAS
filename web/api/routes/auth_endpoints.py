"""Authentication endpoints — login, token refresh"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.auth import (
    USERS_DB,
    verify_password,
    create_access_token,
    require_auth,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse, summary="Login and get JWT token")
async def login(req: LoginRequest):
    """Authenticate with username/password and receive a JWT Bearer token."""
    user = USERS_DB.get(req.username)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(req.username, user["role"])
    return TokenResponse(access_token=token)


@router.get("/me", summary="Get current user info")
async def whoami(user=Depends(require_auth)):
    """Return the authenticated user's info."""
    return {"username": user["username"], "role": user["role"]}
