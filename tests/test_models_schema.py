"""Prueba de que solo escribimos en el schema PostgreSQL `marketplace` (minúsculas)."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.core.config import get_settings
from app.db.base import SCHEMA, Base
import app.models  # noqa: F401

EXPECTED_SCHEMA = "marketplace"

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


def test_db_schema_is_lowercase_marketplace():
    settings = get_settings()
    assert settings.db_schema == EXPECTED_SCHEMA
    assert SCHEMA == EXPECTED_SCHEMA
    assert SCHEMA.islower()
    assert SCHEMA != "Marketplace"


def test_all_orm_tables_bound_only_to_marketplace():
    table_names = {t.name for t in Base.metadata.tables.values()}
    missing = APP_TABLES - table_names
    assert not missing, f"Faltan modelos: {sorted(missing)}"

    for key, table in Base.metadata.tables.items():
        assert table.schema == EXPECTED_SCHEMA, (
            f"{key}: schema esperado {EXPECTED_SCHEMA!r}, got {table.schema!r}"
        )
        assert key.startswith(f"{EXPECTED_SCHEMA}."), (
            f"metadata key debe ser '{EXPECTED_SCHEMA}.…', got {key!r}"
        )


def test_compiled_ddl_targets_marketplace_not_public():
    dialect = postgresql.dialect()
    for table in Base.metadata.tables.values():
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert EXPECTED_SCHEMA in ddl, ddl
        assert f"TABLE {EXPECTED_SCHEMA}." in ddl or f'TABLE "{EXPECTED_SCHEMA}".' in ddl, ddl
        assert "TABLE public." not in ddl
        assert 'TABLE "public".' not in ddl


def test_migration_creates_only_marketplace_schema():
    migration = Path("alembic/versions/0001_init_marketplace.py").read_text(encoding="utf-8")
    assert 'SCHEMA = "marketplace"' in migration
    assert "schema=SCHEMA" in migration
    assert "CREATE SCHEMA IF NOT EXISTS" in migration
    assert "Marketplace" not in migration.replace("marketplace", "")


def test_all_migrations_target_marketplace_schema():
    for path in Path("alembic/versions").glob("*.py"):
        migration = path.read_text(encoding="utf-8")
        assert 'SCHEMA = "marketplace"' in migration, path.name
        assert "schema=SCHEMA" in migration, path.name
        assert "Marketplace" not in migration.replace("marketplace", ""), path.name
