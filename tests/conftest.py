"""Fixtures compartidas."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import SCHEMA, Base
from app.db.session import get_db
from app.main import app
from app.core.config import get_settings
from app.modules.auth.service import get_auth_service


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(_type, _compiler, **_kw):
    return "JSON"


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requiere PostgreSQL accesible")


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def db_engine(settings):
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL no disponible ({settings.database_url}): {exc}")
    yield engine
    engine.dispose()


class FakeAuthService:
    def __init__(self):
        self.created_users: list[dict] = []
        self.updated_passwords: list[tuple[str, str]] = []
        self.recovery_requests: list[str] = []
        self.password_updates: list[tuple[str, str]] = []
        self.fail_login = False
        self.fail_recovery_confirm = False

    def sign_up_buyer(self, email: str, password: str, metadata: dict) -> dict:
        user_id = f"auth-{len(self.created_users) + 1}"
        self.created_users.append({"id": user_id, "email": email, "password": password, "metadata": metadata})
        return {"user": {"id": user_id, "email": email}, "access_token": f"token-{user_id}", "refresh_token": "refresh"}

    def sign_in_with_password(self, email: str, password: str) -> dict:
        if self.fail_login or password == "wrong":
            from app.modules.auth.service import AuthServiceError

            raise AuthServiceError("Invalid login credentials", 401)
        return {"user": {"id": getattr(self, "login_user_id", "auth-login"), "email": email}, "access_token": "token-login", "refresh_token": "refresh"}

    def send_password_recovery(self, email: str) -> dict:
        self.recovery_requests.append(email)
        return {}

    def update_user_password(self, bearer_token: str, new_password: str) -> dict:
        if self.fail_recovery_confirm:
            from app.modules.auth.service import AuthServiceError

            raise AuthServiceError("Token expirado", 401)
        self.password_updates.append((bearer_token, new_password))
        return {}

    def admin_create_user(self, email: str, temporary_password: str, metadata: dict) -> dict:
        user_id = f"admin-auth-{len(self.created_users) + 1}"
        self.created_users.append({"id": user_id, "email": email, "password": temporary_password, "metadata": metadata})
        return {"id": user_id, "email": email}

    def admin_update_user_password(self, user_id: str, temporary_password: str) -> dict:
        self.updated_passwords.append((user_id, temporary_password))
        return {}


@pytest.fixture()
def api_context(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def attach_marketplace(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("ATTACH DATABASE ':memory:' AS marketplace")
        except Exception:
            pass
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    fake_auth = FakeAuthService()
    token_map: dict[str, str] = {}

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def fake_verify_token(token: str) -> dict:
        user_id = token_map[token]
        return {"sub": user_id, "email": f"{user_id}@example.com"}

    def token_for(user_id: str) -> dict[str, str]:
        token = f"token-{user_id}"
        token_map[token] = user_id
        return {"Authorization": f"Bearer {token}"}

    from app.modules.auth import deps as auth_deps

    monkeypatch.setattr(auth_deps, "verify_token", fake_verify_token)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    client = TestClient(app)
    try:
        yield client, db, fake_auth, token_for
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def _integration_url() -> str | None:
    """URL de la BD de test dedicada para los tests de integración de la Épica 10.

    Nunca se usa `settings.database_url` directamente: apunta a Supabase de producción.
    Se exige `TEST_DATABASE_URL` explícito y distinto de producción para no ejecutar DDL
    destructiva (create/drop schema) contra datos reales. Sin él, los tests se saltan.
    """
    test_url = os.getenv("TEST_DATABASE_URL")
    if not test_url:
        return None
    prod_url = get_settings().database_url
    if test_url == prod_url:
        return None
    if "supabase.com" in test_url and os.getenv("ALLOW_SUPABASE_TEST") != "1":
        # Guarda de seguridad: no correr contra infraestructura de producción por accidente.
        return None
    return test_url


@pytest.fixture()
def integration_context(monkeypatch):
    """API real (TestClient) contra PostgreSQL real dedicado (Épica 10, HU-PAG-*).

    Enrutamiento, validación Pydantic y persistencia son reales. Solo se mockean los
    servicios de borde que no son la API bajo prueba: verificación de JWT (Supabase Auth),
    almacenamiento de comprobantes (Supabase Storage) y correo (Resend). El esquema
    `marketplace` se recrea por test para aislamiento total.
    """
    test_url = _integration_url()
    if not test_url:
        pytest.skip(
            "Define TEST_DATABASE_URL con una BD PostgreSQL de test dedicada (distinta de "
            "producción) para correr los tests de integración de pagos."
        )

    engine = create_engine(test_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL de test no disponible ({test_url}): {exc}")

    with engine.begin() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))
        conn.execute(text(f'CREATE SCHEMA "{SCHEMA}"'))
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    fake_auth = FakeAuthService()
    token_map: dict[str, str] = {}
    mail_calls: list[dict] = []

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def fake_verify_token(token: str) -> dict:
        user_id = token_map[token]
        return {"sub": user_id, "email": f"{user_id}@example.com"}

    def token_for(user_id: str) -> dict[str, str]:
        token = f"token-{user_id}"
        token_map[token] = user_id
        return {"Authorization": f"Bearer {token}"}

    def fake_send_email(to, subject, html):
        mail_calls.append({"to": to, "subject": subject})

    from app.modules.auth import deps as auth_deps
    from app.modules.common import mailer
    from app.modules.orders import router as orders_router
    from app.modules.seller import router as seller_router

    monkeypatch.setattr(auth_deps, "verify_token", fake_verify_token)
    # Borde: correo (Resend). Registramos las notificaciones sin enviarlas.
    monkeypatch.setattr(mailer, "send_email", fake_send_email)
    # Borde: almacenamiento de comprobantes (Supabase Storage).
    monkeypatch.setattr(orders_router, "upload_receipt", lambda content, content_type, store_id, order_id: f"{store_id}/{order_id}/receipt.pdf")
    monkeypatch.setattr(orders_router, "signed_url", lambda path, expires_in=3600: (f"https://storage.test/{path}" if path else None))
    monkeypatch.setattr(seller_router, "signed_url", lambda path, expires_in=3600: (f"https://storage.test/{path}" if path else None))

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    client = TestClient(app)
    try:
        yield client, db, token_for, mail_calls
    finally:
        app.dependency_overrides.clear()
        db.close()
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))
        engine.dispose()


@pytest.fixture()
def real_db_context(monkeypatch):
    """API real (TestClient) contra la BD real con aislamiento por transacción y rollback.

    Autorizado por el usuario para correr sobre la BD de producción (aún sin información
    relevante). GARANTÍA DE LIMPIEZA: se abre una transacción externa y la sesión se liga a
    ella con SAVEPOINTs; los `commit()` de los endpoints solo liberan el savepoint, nunca la
    transacción externa, y el teardown hace `rollback` → NADA queda persistido. No se ejecuta
    ningún DDL destructivo (nada de DROP/TRUNCATE). Requiere que la migración de la épica ya
    esté aplicada en la BD (las tablas deben existir).
    """
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        connection = engine.connect()  # pool_pre_ping valida la conexión; no ejecutar SELECT aquí (autobegin)
    except OperationalError as exc:
        engine.dispose()
        pytest.skip(f"BD no disponible para pruebas de integración: {exc}")

    transaction = connection.begin()
    # SQLAlchemy 2.0: la sesión se une a la transacción externa creando SAVEPOINTs; los
    # commit() de los endpoints solo liberan/reinician el savepoint, nunca la transacción
    # externa. El rollback del teardown revierte TODO → cero persistencia.
    TestingSessionLocal = sessionmaker(
        bind=connection, autoflush=False, autocommit=False, join_transaction_mode="create_savepoint"
    )
    db = TestingSessionLocal()

    fake_auth = FakeAuthService()
    token_map: dict[str, str] = {}
    mail_calls: list[dict] = []

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def fake_verify_token(token: str) -> dict:
        user_id = token_map[token]
        return {"sub": user_id, "email": f"{user_id}@example.com"}

    def token_for(user_id: str) -> dict[str, str]:
        token = f"token-{user_id}"
        token_map[token] = user_id
        return {"Authorization": f"Bearer {token}"}

    def fake_send_email(to, subject, html):
        mail_calls.append({"to": to, "subject": subject})

    from app.modules.auth import deps as auth_deps
    from app.modules.common import mailer
    from app.modules.orders import router as orders_router
    from app.modules.seller import router as seller_router

    monkeypatch.setattr(auth_deps, "verify_token", fake_verify_token)
    monkeypatch.setattr(mailer, "send_email", fake_send_email)
    monkeypatch.setattr(orders_router, "upload_receipt", lambda content, ct, sid, oid: f"{sid}/{oid}/r.pdf")
    monkeypatch.setattr(orders_router, "signed_url", lambda p, expires_in=3600: None)
    monkeypatch.setattr(seller_router, "signed_url", lambda p, expires_in=3600: None)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    client = TestClient(app)
    try:
        yield client, db, token_for, mail_calls
    finally:
        app.dependency_overrides.clear()
        db.close()
        transaction.rollback()  # revierte TODO lo creado por los tests: cero persistencia
        connection.close()
        engine.dispose()
