"""Authentication + role-based access control.

- Bearer JWT (HS256) with 8h access token lifetime.
- Bcrypt password hashing.
- Roles: admin > analyst > viewer.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"
VALID_ROLES = {ROLE_ADMIN, ROLE_ANALYST, ROLE_VIEWER}

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 8 * 60  # 8 hours


_client = AsyncIOMotorClient(os.environ["MONGO_URL"])
_db: AsyncIOMotorDatabase = _client[os.environ["DB_NAME"]]


def get_db() -> AsyncIOMotorDatabase:
    return _db


def _jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def _sanitize(user: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(user)
    out.pop("password_hash", None)
    out.pop("_id", None)
    return out


async def get_current_user(request: Request) -> Dict[str, Any]:
    # 1. Bearer header
    token: Optional[str] = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    # 2. Cookie fallback
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await _db.users.find_one({"user_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _sanitize(user)


def require_role(*roles: str):
    """FastAPI dependency factory that requires the current user to have one of `roles`."""
    allowed = set(roles)

    async def _guard(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {sorted(allowed)}",
            )
        return user

    return _guard


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.alerts.create_index("alert_id", unique=True)


async def seed_user(db: AsyncIOMotorDatabase, email: str, password: str, role: str, name: str) -> None:
    if role not in VALID_ROLES:
        raise ValueError(f"invalid role {role}")
    email = email.strip().lower()
    existing = await db.users.find_one({"email": email})
    if existing is None:
        await db.users.insert_one(
            {
                "user_id": f"u_{uuid.uuid4().hex[:12]}",
                "email": email,
                "name": name,
                "role": role,
                "password_hash": hash_password(password),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    else:
        updates: Dict[str, Any] = {}
        if existing.get("role") != role:
            updates["role"] = role
        if not verify_password(password, existing.get("password_hash", "")):
            updates["password_hash"] = hash_password(password)
        if updates:
            await db.users.update_one({"_id": existing["_id"]}, {"$set": updates})


async def seed_default_users(db: AsyncIOMotorDatabase) -> None:
    await seed_user(
        db,
        os.environ.get("ADMIN_EMAIL", "admin@fraudops.io"),
        os.environ.get("ADMIN_PASSWORD", "admin123"),
        ROLE_ADMIN,
        "Admin",
    )
    await seed_user(
        db,
        os.environ.get("ANALYST_EMAIL", "analyst@fraudops.io"),
        os.environ.get("ANALYST_PASSWORD", "analyst123"),
        ROLE_ANALYST,
        "Analyst",
    )
    await seed_user(
        db,
        os.environ.get("VIEWER_EMAIL", "viewer@fraudops.io"),
        os.environ.get("VIEWER_PASSWORD", "viewer123"),
        ROLE_VIEWER,
        "Viewer",
    )
