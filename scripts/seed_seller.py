"""Crea o actualiza el vendedor demo y lo vincula a la tienda Singular.

Uso: python -m scripts.seed_seller
"""

import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Store, StoreMember, User
from app.models.user import UserRole
from scripts.seed_admin import ensure_auth_user

settings = get_settings()


def main() -> None:
    if not settings.seller_email or not settings.seller_password:
        sys.exit("SELLER_EMAIL y SELLER_PASSWORD deben estar definidos en .env")
    if not settings.supabase_url or not settings.supabase_service_role_key:
        sys.exit("SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY deben estar definidos en .env")

    auth_id = ensure_auth_user(settings.seller_email, settings.seller_password)
    with SessionLocal() as db:
        store = db.scalar(select(Store).where(Store.slug == "singular"))
        if store is None:
            sys.exit("No existe la tienda Singular. Ejecuta primero python -m scripts.seed_demo_catalog")

        user = db.get(User, auth_id)
        if user is None:
            user = User(id=auth_id, email=settings.seller_email, name="Vendedor Singular", role=UserRole.seller)
            db.add(user)
        else:
            user.role = UserRole.seller
            user.active = True

        member = db.scalar(select(StoreMember).where(StoreMember.store_id == store.id, StoreMember.user_id == auth_id))
        if member is None:
            db.add(StoreMember(store_id=store.id, user_id=auth_id, role="owner"))
        db.commit()

    print(f"Vendedor listo: {settings.seller_email}")


if __name__ == "__main__":
    main()
