"""pricing promotions for Epica 05

Revision ID: 0009_pricing_promotions
Revises: 0008_product_variant_images
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_pricing_promotions"
down_revision: Union[str, None] = "0008_product_variant_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    promotion_scope = postgresql.ENUM(
        "store", "products", name="promotion_scope", schema=SCHEMA, create_type=False
    )
    charge_type = postgresql.ENUM("fixed", "percent", name="charge_type", schema=SCHEMA, create_type=False)
    adjustment_kind = postgresql.ENUM(
        "discount", "extra_charge", name="order_adjustment_kind", schema=SCHEMA, create_type=False
    )
    promotion_scope.create(op.get_bind(), checkfirst=True)
    charge_type.create(op.get_bind(), checkfirst=True)
    adjustment_kind.create(op.get_bind(), checkfirst=True)

    op.add_column("product_variants", sa.Column("special_price", sa.Integer(), nullable=True), schema=SCHEMA)
    op.add_column(
        "product_variants",
        sa.Column("special_starts_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "product_variants",
        sa.Column("special_ends_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )

    op.add_column(
        "promotions",
        sa.Column("pay_quantity", sa.Integer(), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "promotions",
        sa.Column("scope", promotion_scope, nullable=False, server_default="store"),
        schema=SCHEMA,
    )
    op.add_column(
        "promotions",
        sa.Column("product_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        schema=SCHEMA,
    )
    op.alter_column("promotions", "scope", server_default=None, schema=SCHEMA)
    op.alter_column("promotions", "product_ids", server_default=None, schema=SCHEMA)

    op.add_column(
        "coupons",
        sa.Column("scope", promotion_scope, nullable=False, server_default="store"),
        schema=SCHEMA,
    )
    op.add_column(
        "coupons",
        sa.Column("product_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        schema=SCHEMA,
    )
    op.alter_column("coupons", "scope", server_default=None, schema=SCHEMA)
    op.alter_column("coupons", "product_ids", server_default=None, schema=SCHEMA)

    op.create_table(
        "extra_charges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("charge_type", charge_type, nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("scope", promotion_scope, nullable=False),
        sa.Column("product_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_extra_charges_store_id", "extra_charges", ["store_id"], schema=SCHEMA)

    op.create_table(
        "order_adjustments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("kind", adjustment_kind, nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_order_adjustments_order_id", "order_adjustments", ["order_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_order_adjustments_order_id", table_name="order_adjustments", schema=SCHEMA)
    op.drop_table("order_adjustments", schema=SCHEMA)
    op.drop_index("ix_extra_charges_store_id", table_name="extra_charges", schema=SCHEMA)
    op.drop_table("extra_charges", schema=SCHEMA)
    op.drop_column("coupons", "product_ids", schema=SCHEMA)
    op.drop_column("coupons", "scope", schema=SCHEMA)
    op.drop_column("promotions", "product_ids", schema=SCHEMA)
    op.drop_column("promotions", "scope", schema=SCHEMA)
    op.drop_column("promotions", "pay_quantity", schema=SCHEMA)
    op.drop_column("product_variants", "special_ends_at", schema=SCHEMA)
    op.drop_column("product_variants", "special_starts_at", schema=SCHEMA)
    op.drop_column("product_variants", "special_price", schema=SCHEMA)
    sa.Enum(name="order_adjustment_kind", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="charge_type", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="promotion_scope", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
