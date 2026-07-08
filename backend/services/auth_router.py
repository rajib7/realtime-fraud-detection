"""Auth router — /api/auth/{register,login,me,logout}."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field

from .auth import (
    ROLE_VIEWER,
    VALID_ROLES,
    create_access_token,
    get_current_user,
    get_db,
    hash_password,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field("", max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


def _sanitize(u: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user_id": u["user_id"],
        "email": u["email"],
        "name": u.get("name", ""),
        "role": u.get("role", ROLE_VIEWER),
        "created_at": u.get("created_at"),
    }


@router.post("/register")
async def register(payload: RegisterIn, response: Response) -> Dict[str, Any]:
    db = get_db()
    email = payload.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = {
        "user_id": f"u_{uuid.uuid4().hex[:12]}",
        "email": email,
        "name": payload.name or email.split("@")[0],
        "role": ROLE_VIEWER,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user)
    token = create_access_token(user["user_id"], user["email"], user["role"])
    response.set_cookie(
        "access_token", token, httponly=True, secure=False, samesite="lax", max_age=8 * 3600, path="/"
    )
    return {"user": _sanitize(user), "access_token": token, "token_type": "Bearer"}


@router.post("/login")
async def login(payload: LoginIn, response: Response) -> Dict[str, Any]:
    db = get_db()
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["user_id"], user["email"], user["role"])
    response.set_cookie(
        "access_token", token, httponly=True, secure=False, samesite="lax", max_age=8 * 3600, path="/"
    )
    return {"user": _sanitize(user), "access_token": token, "token_type": "Bearer"}


@router.post("/logout")
async def logout(response: Response, _user=Depends(get_current_user)) -> Dict[str, Any]:
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@router.get("/me")
async def me(user=Depends(get_current_user)) -> Dict[str, Any]:
    return {"user": _sanitize(user)}


@router.get("/roles")
async def roles() -> Dict[str, Any]:
    return {"roles": sorted(VALID_ROLES)}
