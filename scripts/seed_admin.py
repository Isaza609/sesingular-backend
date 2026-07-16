"""Seed idempotente del administrador de plataforma.

1. Crea (o encuentra) el usuario en Supabase Auth con ADMIN_EMAIL/ADMIN_PASSWORD.
2. Inserta/actualiza la fila correspondiente en marketplace.users con rol admin.

Uso:  python -m scripts.seed_admin
"""

from __future__ import annotations

import sys

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import User
from app.models.user import UserRole

settings = get_settings()


def _admin_headers() -> dict:
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


def ensure_auth_user(email: str, password: str) -> str:
    """Devuelve el id del usuario en Supabase Auth, creándolo si no existe."""
    base = settings.supabase_url.rstrip("/")

    resp = httpx.post(
        f"{base}/auth/v1/admin/users",
        headers=_admin_headers(),
        json={"email": email, "password": password, "email_confirm": True},
        timeout=15.0,
    )
    if resp.status_code in (200, 201):
        return resp.json()["id"]

    # Ya existe (u otro error): buscarlo en el listado
    page = 1
    while page <= 20:
        listing = httpx.get(
            f"{base}/auth/v1/admin/users",
            headers=_admin_headers(),
            params={"page": page, "per_page": 100},
            timeout=15.0,
        )
        listing.raise_for_status()
        users = listing.json().get("users", [])
        if not users:
            break
        for user in users:
            if (user.get("email") or "").lower() == email.lower():
                return user["id"]
        page += 1

    raise RuntimeError(f"No se pudo crear ni encontrar el usuario auth: {resp.status_code} {resp.text}")


def main() -> None:
    email = settings.admin_email
    password = settings.admin_password
    if not email or not password:
        sys.exit("ADMIN_EMAIL y ADMIN_PASSWORD deben estar definidos en .env")
    if not settings.supabase_url or not settings.supabase_service_role_key:
        sys.exit("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY deben estar definidos en .env")

    auth_id = ensure_auth_user(email, password)
    print(f"Usuario Supabase Auth: {auth_id}")

    with SessionLocal() as db:
        user = db.get(User, auth_id)
        if user is None:
            # Si existía una fila con otro id para el mismo email, se realinea al id de Auth
            legacy = db.scalar(select(User).where(User.email == email))
            if legacy is not None:
                db.delete(legacy)
                db.flush()
            user = User(id=auth_id, email=email, name="Administrador", role=UserRole.admin)
            db.add(user)
            action = "creado"
        else:
            user.role = UserRole.admin
            user.active = True
            action = "actualizado"
        db.commit()
    print(f"Usuario admin {action} en marketplace.users ({email})")


if __name__ == "__main__":
    main()
