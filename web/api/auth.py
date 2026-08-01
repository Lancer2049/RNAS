"""JWT authentication module for RNAS API

Phase 0 security hardening — Bearer Token authentication.
Production readiness requires replacing the in-memory USERS_DB with a
persistent store (SQLite or file-based).

Environment variables:
    RNAS_JWT_SECRET    — JWT signing key (auto-generated if unset)
    RNAS_ADMIN_PASS    — initial admin password (auto-generated if unset)
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get("RNAS_JWT_SECRET", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("RNAS_JWT_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

# ---------------------------------------------------------------------------
# User store (in-memory — replace with SQLite/file for production)
# ---------------------------------------------------------------------------

def _load_or_create_password() -> str:
    """Return the persistent admin password.

    Priority: RNAS_ADMIN_PASS env → persisted file → generate + persist.
    Persisting avoids locking out the admin after a restart (a fresh
    random password was previously generated on every process start).
    """
    pw = os.environ.get("RNAS_ADMIN_PASS")
    if pw:
        return pw

    pw_file = Path("/etc/rnas/.admin_password")
    try:
        if pw_file.exists():
            stored = pw_file.read_text().strip()
            if stored:
                return stored
    except OSError:
        pass

    pw = secrets.token_urlsafe(12)
    try:
        pw_file.parent.mkdir(parents=True, exist_ok=True)
        pw_file.write_text(pw)
        pw_file.chmod(0o600)
    except OSError:
        pass
    return pw


ADMIN_PASSWORD = _load_or_create_password()

USERS_DB: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash(ADMIN_PASSWORD),
        "role": "admin",
    }
}

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str, role: str = "admin") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[dict]:
    """Return current user dict, or None if no/invalid token.

    Use for endpoints that *optionally* support auth (e.g. health, WebSocket).
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_auth(user=Depends(get_current_user)) -> dict:
    """Mandatory auth dependency — returns 401 if not authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# RBAC roles: viewer < operator < admin
ROLE_RANK = {"viewer": 1, "operator": 2, "admin": 3}


def require_role(min_role: str = "operator"):
    """Factory for role-gated endpoints.

    Usage: user=Depends(require_role("admin"))
    viewer: read-only; operator: + diagnostics/config; admin: everything.
    """
    def _dependency(user=Depends(require_auth)) -> dict:
        role = user.get("role", "viewer")
        if ROLE_RANK.get(role, 0) < ROLE_RANK.get(min_role, 2):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_role} role (current: {role})",
            )
        return user
    return _dependency


# ---------------------------------------------------------------------------
# Feature flags for high-risk endpoints
# ---------------------------------------------------------------------------

FEATURE_FLAGS = {
    "web_terminal": os.environ.get("RNAS_FEATURE_TERMINAL", "false").lower() == "true",
    "packet_capture": os.environ.get("RNAS_FEATURE_CAPTURE", "false").lower() == "true",
    "bandwidth_test": os.environ.get("RNAS_FEATURE_BANDWIDTH", "false").lower() == "true",
}
