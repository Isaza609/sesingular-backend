"""Dependencias de autenticación/autorización para los routers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.models.user import UserRole
from app.modules.auth.supabase import SupabaseAuthError, verify_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token requerido")
    try:
        claims = verify_token(credentials.credentials)
    except SupabaseAuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token inválido: {exc}") from exc

    user = db.get(User, claims["sub"])
    if user is None:
        metadata = claims.get("user_metadata") or {}
        email = claims.get("email") or f"{claims['sub']}@invalid.local"
        user = User(
            id=claims["sub"],
            email=email,
            name=metadata.get("full_name") or metadata.get("name") or email.split("@")[0],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario desactivado")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Requiere rol admin")
    return user
