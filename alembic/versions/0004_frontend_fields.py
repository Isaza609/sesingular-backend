"""product display fields, user loyalty fields, favorites

Revision ID: 0004_frontend_fields
Revises: 0003_commerce_admin
Create Date: 2026-07-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_frontend_fields"
down_revision: Union[str, None] = "0003_commerce_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    # Campos de presentación del producto (los que el frontend ya muestra).
    op.add_column("products", sa.Column("material", sa.String(length=120), nullable=True), schema=SCHEMA)
    op.add_column("products", sa.Column("badge", sa.String(length=20), nullable=True), schema=SCHEMA)
    op.add_column(
        "products",
        sa.Column("bestseller", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        schema=SCHEMA,
    )

    # Fidelización del comprador.
    op.add_column(
        "users",
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        schema=SCHEMA,
    )
    op.add_column("users", sa.Column("tier", sa.String(length=60), nullable=True), schema=SCHEMA)

    # Favoritos (wishlist) por usuario.
    op.create_table(
        "favorites",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], [f"{SCHEMA}.products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_favorites_user_product"),
        schema=SCHEMA,
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"], schema=SCHEMA)
    op.create_index("ix_favorites_product_id", "favorites", ["product_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("favorites", schema=SCHEMA)
    op.drop_column("users", "tier", schema=SCHEMA)
    op.drop_column("users", "points", schema=SCHEMA)
    op.drop_column("products", "bestseller", schema=SCHEMA)
    op.drop_column("products", "badge", schema=SCHEMA)
    op.drop_column("products", "material", schema=SCHEMA)
