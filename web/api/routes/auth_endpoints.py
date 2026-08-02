"""Authentication endpoints — login, token, user management (RBAC).

Users persist to /etc/rnas/users.json so role/password changes survive
restarts (USERS_DB in api.auth is the in-memory seed; this module reads
and writes the persistent copy).
"""

import json
import threading
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.auth import (
    USERS_DB,
    verify_password,
    create_access_token,
    require_auth,
    require_role,
    pwd_context,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

USERS_FILE = Path("/etc/rnas/users.json")
_lock = threading.Lock()


def _load_users() -> dict:
    """Return the merged user store (seeded + persisted)."""
    with _lock:
        try:
            if USERS_FILE.exists():
                persisted = json.loads(USERS_FILE.read_text())
                USERS_DB.update(persisted)
        except Exception:
            pass
        return USERS_DB


def _save_users():
    with _lock:
        try:
            USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            USERS_FILE.write_text(json.dumps(USERS_DB, indent=2))
        except Exception:
            pass


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None


@router.post("/token", response_model=TokenResponse, summary="Login and get JWT token")
async def login(req: LoginRequest):
    """Authenticate with username/password and receive a JWT Bearer token."""
    users = _load_users()
    user = users.get(req.username)
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


# ── Admin: user management ───────────────────────────────────────────────

@router.get("/users", summary="List users (admin)")
async def list_users(user=Depends(require_role("admin"))):
    users = _load_users()
    return {"users": [
        {"username": u["username"], "role": u["role"]}
        for u in users.values()
    ]}


@router.post("/users", summary="Create user (admin)")
async def create_user(req: UserCreate, user=Depends(require_role("admin"))):
    username = req.username.strip()
    if not username or not req.password:
        raise HTTPException(400, "username and password required")
    if username in _load_users():
        raise HTTPException(409, f"user {username} exists")
    if req.role not in ("viewer", "operator", "admin"):
        raise HTTPException(400, "role must be viewer/operator/admin")
    USERS_DB[username] = {
        "username": username,
        "hashed_password": pwd_context.hash(req.password),
        "role": req.role,
    }
    _save_users()
    from services.audit import record
    record(user["username"], "user_create", username, {"role": req.role})
    return {"status": "created", "username": username, "role": req.role}


@router.put("/users/{username}", summary="Update user password/role (admin)")
async def update_user(username: str, req: UserUpdate, user=Depends(require_role("admin"))):
    users = _load_users()
    if username not in users:
        raise HTTPException(404, f"user {username} not found")
    if req.role is not None:
        if req.role not in ("viewer", "operator", "admin"):
            raise HTTPException(400, "role must be viewer/operator/admin")
        users[username]["role"] = req.role
    if req.password:
        users[username]["hashed_password"] = pwd_context.hash(req.password)
    _save_users()
    from services.audit import record
    record(user["username"], "user_update", username,
           {"role": req.role, "password_changed": bool(req.password)})
    return {"status": "updated", "username": username}


@router.delete("/users/{username}", summary="Delete user (admin)")
async def delete_user(username: str, user=Depends(require_role("admin"))):
    if username == "admin":
        raise HTTPException(400, "cannot delete the admin user")
    users = _load_users()
    if username not in users:
        raise HTTPException(404, f"user {username} not found")
    del users[username]
    _save_users()
    from services.audit import record
    record(user["username"], "user_delete", username)
    return {"status": "deleted", "username": username}
