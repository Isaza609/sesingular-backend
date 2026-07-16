"""init marketplace schema

Revision ID: 0001_init_marketplace
Revises:
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init_marketplace"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

    user_role = postgresql.ENUM(
        "buyer", "seller", "admin", name="user_role", schema=SCHEMA, create_type=False
    )
    product_status = postgresql.ENUM(
        "draft",
        "active",
        "out_of_stock",
        "discontinued",
        name="product_status",
        schema=SCHEMA,
        create_type=False,
    )
    inventory_reason = postgresql.ENUM(
        "reserve",
        "release",
        "sale",
        "adjust",
        "restock",
        "return_in",
        name="inventory_reason",
        schema=SCHEMA,
        create_type=False,
    )
    # Crear enums una sola vez (create_type=False evita duplicarlos al crear tablas)
    postgresql.ENUM(
        "buyer", "seller", "admin", name="user_role", schema=SCHEMA
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "draft", "active", "out_of_stock", "discontinued", name="product_status", schema=SCHEMA
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "reserve",
        "release",
        "sale",
        "adjust",
        "restock",
        "return_in",
        name="inventory_reason",
        schema=SCHEMA,
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True, schema=SCHEMA)

    op.create_table(
        "stores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("contact_phone", sa.String(length=40), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_stores_slug", "stores", ["slug"], unique=True, schema=SCHEMA)

    op.create_table(
        "store_members",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "user_id", name="uq_store_members_store_user"),
        schema=SCHEMA,
    )
    op.create_index("ix_store_members_store_id", "store_members", ["store_id"], schema=SCHEMA)
    op.create_index("ix_store_members_user_id", "store_members", ["user_id"], schema=SCHEMA)

    op.create_table(
        "warehouses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address_line", sa.String(length=300), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_warehouses_store_id", "warehouses", ["store_id"], schema=SCHEMA)

    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], [f"{SCHEMA}.categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "slug", name="uq_categories_store_slug"),
        schema=SCHEMA,
    )
    op.create_index("ix_categories_store_id", "categories", ["store_id"], schema=SCHEMA)
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"], schema=SCHEMA)

    op.create_table(
        "products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("short_desc", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", product_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "slug", name="uq_products_store_slug"),
        schema=SCHEMA,
    )
    op.create_index("ix_products_store_id", "products", ["store_id"], schema=SCHEMA)

    op.create_table(
        "product_categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("category_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], [f"{SCHEMA}.categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], [f"{SCHEMA}.products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "category_id", name="uq_product_categories"),
        schema=SCHEMA,
    )
    op.create_index("ix_product_categories_product_id", "product_categories", ["product_id"], schema=SCHEMA)
    op.create_index("ix_product_categories_category_id", "product_categories", ["category_id"], schema=SCHEMA)

    op.create_table(
        "product_variants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("color", sa.String(length=80), nullable=True),
        sa.Column("size", sa.String(length=80), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("compare_at", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], [f"{SCHEMA}.products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "sku", name="uq_product_variants_product_sku"),
        schema=SCHEMA,
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"], schema=SCHEMA)

    op.create_table(
        "product_images",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("alt", sa.String(length=200), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], [f"{SCHEMA}.products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"], schema=SCHEMA)

    op.create_table(
        "stock_levels",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("variant_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["variant_id"], [f"{SCHEMA}.product_variants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("variant_id", "warehouse_id", name="uq_stock_levels_variant_warehouse"),
        schema=SCHEMA,
    )
    op.create_index("ix_stock_levels_variant_id", "stock_levels", ["variant_id"], schema=SCHEMA)
    op.create_index("ix_stock_levels_warehouse_id", "stock_levels", ["warehouse_id"], schema=SCHEMA)

    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("variant_id", sa.String(length=36), nullable=False),
        sa.Column("warehouse_id", sa.String(length=36), nullable=True),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", inventory_reason, nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["variant_id"], [f"{SCHEMA}.product_variants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_inventory_movements_variant_id", "inventory_movements", ["variant_id"], schema=SCHEMA)
    op.create_index(
        "ix_inventory_movements_warehouse_id", "inventory_movements", ["warehouse_id"], schema=SCHEMA
    )
    op.create_index("ix_inventory_movements_order_id", "inventory_movements", ["order_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("inventory_movements", schema=SCHEMA)
    op.drop_table("stock_levels", schema=SCHEMA)
    op.drop_table("product_images", schema=SCHEMA)
    op.drop_table("product_variants", schema=SCHEMA)
    op.drop_table("product_categories", schema=SCHEMA)
    op.drop_table("products", schema=SCHEMA)
    op.drop_table("categories", schema=SCHEMA)
    op.drop_table("warehouses", schema=SCHEMA)
    op.drop_table("store_members", schema=SCHEMA)
    op.drop_table("stores", schema=SCHEMA)
    op.drop_table("users", schema=SCHEMA)

    sa.Enum(name="inventory_reason", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="product_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)

    op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))
