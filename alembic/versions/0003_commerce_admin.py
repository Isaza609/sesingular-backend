"""carts, promotions, coupons, reviews, disputes, platform_settings

Revision ID: 0003_commerce_admin
Revises: 0002_orders_payments_shipping
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_commerce_admin"
down_revision: Union[str, None] = "0002_orders_payments_shipping"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    discount_type = postgresql.ENUM(
        "percent", "fixed", "volume", name="discount_type", schema=SCHEMA, create_type=False
    )
    review_status = postgresql.ENUM(
        "published", "pending", "hidden", name="review_status", schema=SCHEMA, create_type=False
    )
    report_status = postgresql.ENUM(
        "open", "resolved", "dismissed", name="report_status", schema=SCHEMA, create_type=False
    )
    dispute_status = postgresql.ENUM(
        "open", "in_review", "resolved", "rejected", name="dispute_status", schema=SCHEMA, create_type=False
    )
    postgresql.ENUM("percent", "fixed", "volume", name="discount_type", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM("published", "pending", "hidden", name="review_status", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM("open", "resolved", "dismissed", name="report_status", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "open", "in_review", "resolved", "rejected", name="dispute_status", schema=SCHEMA
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "carts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_carts_user_id", "carts", ["user_id"], unique=True, schema=SCHEMA)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("cart_id", sa.String(length=36), nullable=False),
        sa.Column("variant_id", sa.String(length=36), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], [f"{SCHEMA}.carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], [f"{SCHEMA}.product_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_id", "variant_id", name="uq_cart_items_cart_variant"),
        schema=SCHEMA,
    )
    op.create_index("ix_cart_items_cart_id", "cart_items", ["cart_id"], schema=SCHEMA)
    op.create_index("ix_cart_items_variant_id", "cart_items", ["variant_id"], schema=SCHEMA)

    op.create_table(
        "promotions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("discount_type", discount_type, nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("min_quantity", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_promotions_store_id", "promotions", ["store_id"], schema=SCHEMA)

    op.create_table(
        "coupons",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("discount_type", discount_type, nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "code", name="uq_coupons_store_code"),
        schema=SCHEMA,
    )
    op.create_index("ix_coupons_store_id", "coupons", ["store_id"], schema=SCHEMA)

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("status", review_status, nullable=False, server_default="published"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], [f"{SCHEMA}.products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        schema=SCHEMA,
    )
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"], schema=SCHEMA)
    op.create_index("ix_reviews_store_id", "reviews", ["store_id"], schema=SCHEMA)
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"], schema=SCHEMA)
    op.create_index("ix_reviews_status", "reviews", ["status"], schema=SCHEMA)

    op.create_table(
        "review_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("review_id", sa.String(length=36), nullable=False),
        sa.Column("reporter_id", sa.String(length=36), nullable=True),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("status", report_status, nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], [f"{SCHEMA}.reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], [f"{SCHEMA}.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_review_reports_review_id", "review_reports", ["review_id"], schema=SCHEMA)
    op.create_index("ix_review_reports_status", "review_reports", ["status"], schema=SCHEMA)

    op.create_table(
        "disputes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("opened_by", sa.String(length=36), nullable=True),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", dispute_status, nullable=False, server_default="open"),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opened_by"], [f"{SCHEMA}.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_disputes_order_id", "disputes", ["order_id"], schema=SCHEMA)
    op.create_index("ix_disputes_status", "disputes", ["status"], schema=SCHEMA)

    op.create_table(
        "platform_settings",
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=False),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("key"),
        schema=SCHEMA,
    )

    # Valores por defecto de configuración de plataforma
    op.execute(
        sa.text(
            f"""
            INSERT INTO "{SCHEMA}".platform_settings (key, value)
            VALUES
              ('commission', '{{"type": "percent", "value": 10}}'::jsonb),
              ('payment_gateway', '{{"provider": "mercadopago", "sandbox": true, "public_key": "", "webhook_url": ""}}'::jsonb)
            ON CONFLICT (key) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_table("platform_settings", schema=SCHEMA)
    op.drop_table("disputes", schema=SCHEMA)
    op.drop_table("review_reports", schema=SCHEMA)
    op.drop_table("reviews", schema=SCHEMA)
    op.drop_table("coupons", schema=SCHEMA)
    op.drop_table("promotions", schema=SCHEMA)
    op.drop_table("cart_items", schema=SCHEMA)
    op.drop_table("carts", schema=SCHEMA)

    sa.Enum(name="dispute_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="report_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="review_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="discount_type", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
