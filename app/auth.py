import hashlib
from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models.user import User

DEFAULT_PASSWORD = "123456"


def hash_password(password: str) -> str:
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return password == DEFAULT_PASSWORD
    return hash_password(password) == password_hash


def current_user_from_cookie(request: Request, db: Session) -> Optional[User]:
    raw = request.cookies.get("user_id")
    try:
        user_id = int(raw) if raw else None
    except ValueError:
        user_id = None
    if not user_id:
        return None
    return db.get(User, user_id)


def require_login(request: Request, db: Session) -> User | RedirectResponse:
    user = current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return user


def is_admin(user: User | None) -> bool:
    return bool(user and user.role == "admin")
