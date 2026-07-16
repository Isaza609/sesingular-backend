"""Alembic environment — migraciones solo en DB_SCHEMA (marketplace)."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

from app.core.config import get_settings
from app.db.base import Base
import app.models  # noqa: F401 — registra modelos en metadata

config = context.config
settings = get_settings()
SCHEMA = settings.db_schema
# No usar config.set_main_option con la URL: ConfigParser rompe con % en passwords (%23, etc.)
DATABASE_URL = settings.database_url

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    """Ignora objetos fuera del schema de la app (p. ej. public de Supabase)."""
    if type_ == "table":
        return object_.schema == SCHEMA
    if hasattr(object_, "schema") and object_.schema is not None:
        return object_.schema == SCHEMA
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=SCHEMA,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))
        connection.commit()

        connection.execute(text(f'SET search_path TO "{SCHEMA}", public'))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=SCHEMA,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
