from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

SCHEMA = get_settings().db_schema


class Base(DeclarativeBase):
    """Base ORM: metadata fija al schema de la app (marketplace)."""

    metadata = MetaData(schema=SCHEMA)
