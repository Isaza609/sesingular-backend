from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Store, StoreMember, User
from app.models.user import UserRole
from app.modules.auth.deps import ensure_password_change_completed, get_current_user


def require_role(*roles: UserRole):
    """Crea una dependencia que limita una ruta a roles concretos."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        ensure_password_change_completed(user)
        if user.role not in roles:
            labels = ", ".join(role.value for role in roles)
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requiere rol: {labels}")
        return user

    return dependency


require_buyer = require_role(UserRole.buyer)
require_seller = require_role(UserRole.seller)


def get_seller_store(
    user: User = Depends(require_seller), db: Session = Depends(get_db)
) -> Store:
    """Obtiene la tienda del vendedor; la primera membresía es la tienda activa."""

    store = db.scalar(
        select(Store)
        .join(StoreMember, StoreMember.store_id == Store.id)
        .where(StoreMember.user_id == user.id, Store.active.is_(True))
        .order_by(Store.created_at)
    )
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El vendedor no tiene una tienda activa")
    return store


def ensure_store_member(store_id: str, user: User, db: Session) -> Store:
    """Valida que un vendedor solo pueda operar dentro de su propia tienda."""

    if user.role == UserRole.admin:
        store = db.get(Store, store_id)
    else:
        store = db.scalar(
            select(Store)
            .join(StoreMember, StoreMember.store_id == Store.id)
            .where(Store.id == store_id, StoreMember.user_id == user.id)
        )
    if store is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes acceso a esta tienda")
    return store
