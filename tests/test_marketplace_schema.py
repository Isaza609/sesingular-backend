"""Tests de aislamiento del schema marketplace (requieren PostgreSQL)."""

from __future__ import annotations

import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

APP_TABLES = {
    "users",
    "stores",
    "store_members",
    "warehouses",
    "categories",
    "products",
    "product_categories",
    "product_variants",
    "product_images",
    "stock_levels",
    "inventory_movements",
    "addresses",
    "orders",
    "order_items",
    "payments",
    "shipments",
    "carts",
    "cart_items",
    "promotions",
    "coupons",
    "reviews",
    "review_reports",
    "disputes",
    "platform_settings",
}

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def migrated_db(settings, db_engine):
    # env.py ya lee DATABASE_URL desde settings; no usar set_main_option (% en password)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield


def _tables_in_schema(engine, schema: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema
                  AND table_type = 'BASE TABLE'
                """
            ),
            {"schema": schema},
        ).fetchall()
    return {r[0] for r in rows}


def test_app_tables_exist_only_in_marketplace(migrated_db, db_engine, settings):
    schema = settings.db_schema
    assert schema == "marketplace"

    in_marketplace = _tables_in_schema(db_engine, schema)
    missing = APP_TABLES - in_marketplace
    assert not missing, f"Faltan tablas en {schema}: {sorted(missing)}"

    in_public = _tables_in_schema(db_engine, "public")
    leaked = APP_TABLES & in_public
    assert not leaked, f"Tablas de la app no deben estar en public: {sorted(leaked)}"

    # No debe existir el schema con M mayúscula ni tablas de la app ahí
    with db_engine.connect() as conn:
        capital = conn.execute(
            text(
                """
                SELECT nspname FROM pg_namespace
                WHERE nspname = 'Marketplace'
                """
            )
        ).fetchone()
        assert capital is None, "No debe usarse el schema 'Marketplace' (mayúscula)"


def test_alembic_version_table_in_marketplace(migrated_db, db_engine, settings):
    schema = settings.db_schema
    with db_engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = :schema
                  AND table_name = 'alembic_version'
                """
            ),
            {"schema": schema},
        ).fetchone()
        assert row is not None, "alembic_version debe vivir en marketplace"

        version = conn.execute(
            text(f'SELECT version_num FROM "{schema}".alembic_version')
        ).scalar_one()
        assert version == "0003_commerce_admin"


def test_smoke_insert_user_in_marketplace(migrated_db, db_engine, settings):
    schema = settings.db_schema
    user_id = str(uuid.uuid4())
    email = f"schema-test-{user_id[:8]}@example.com"

    with db_engine.begin() as conn:
        conn.execute(text(f'SET search_path TO "{schema}", public'))
        conn.execute(
            text(
                f"""
                INSERT INTO "{schema}".users (id, email, role, name)
                VALUES (:id, :email, 'buyer', 'Schema Test')
                """
            ),
            {"id": user_id, "email": email},
        )
        found = conn.execute(
            text(
                """
                SELECT table_schema
                FROM information_schema.tables
                WHERE table_name = 'users'
                  AND table_schema = :schema
                """
            ),
            {"schema": schema},
        ).scalar_one()
        assert found == schema

        name = conn.execute(
            text(f'SELECT name FROM "{schema}".users WHERE id = :id'),
            {"id": user_id},
        ).scalar_one()
        assert name == "Schema Test"

        conn.execute(
            text(f'DELETE FROM "{schema}".users WHERE id = :id'),
            {"id": user_id},
        )
