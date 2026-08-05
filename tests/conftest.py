"""Fixtures compartidas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
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
