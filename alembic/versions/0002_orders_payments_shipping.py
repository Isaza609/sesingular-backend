"""orders, payments, shipments, addresses + users.active

Revision ID: 0002_orders_payments_shipping
Revises: 0001_init_marketplace
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_orders_payments_shipping"
down_revision: Union[str, None] = "0001_init_marketplace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    order_status = postgresql.ENUM(
        "pending",
        "confirmed",
        "preparing",
        "shipped",
        "delivered",
        "cancelled",
        "returned",
        name="order_status",
        schema=SCHEMA,
        create_type=False,
    )
    sale_channel = postgresql.ENUM(
        "online", "presencial", name="sale_channel", schema=SCHEMA, create_type=False
    )
    payment_status = postgresql.ENUM(
        "pending", "paid", "rejected", "refunded", name="payment_status", schema=SCHEMA, create_type=False
    )
    shipment_status = postgresql.ENUM(
        "pending",
        "in_transit",
        "delivered",
        "returned",
        name="shipment_status",
        schema=SCHEMA,
        create_type=False,
    )
    postgresql.ENUM(
        "pending",
        "confirmed",
        "preparing",
        "shipped",
        "delivered",
        "cancelled",
        "returned",
        name="order_status",
        schema=SCHEMA,
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("online", "presencial", name="sale_channel", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "pending", "paid", "rejected", "refunded", name="payment_status", schema=SCHEMA
    ).create(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        "pending", "in_transit", "delivered", "returned", name="shipment_status", schema=SCHEMA
    ).create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        schema=SCHEMA,
    )

    op.create_table(
        "addresses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=80), nullable=True),
        sa.Column("recipient_name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("address_line", sa.String(length=300), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_addresses_user_id", "addresses", ["user_id"], schema=SCHEMA)

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        # Nullable: ventas POS sin comprador registrado
        sa.Column("buyer_id", sa.String(length=36), nullable=True),
        # Nullable: se asigna después si la tienda tiene más de un almacén
        sa.Column("warehouse_id", sa.String(length=36), nullable=True),
        sa.Column("address_id", sa.String(length=36), nullable=True),
        sa.Column("channel", sale_channel, nullable=False, server_default="online"),
        sa.Column("status", order_status, nullable=False, server_default="pending"),
        sa.Column("subtotal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tax", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["buyer_id"], [f"{SCHEMA}.users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["warehouse_id"], [f"{SCHEMA}.warehouses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["address_id"], [f"{SCHEMA}.addresses.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_orders_store_id", "orders", ["store_id"], schema=SCHEMA)
    op.create_index("ix_orders_buyer_id", "orders", ["buyer_id"], schema=SCHEMA)
    op.create_index("ix_orders_warehouse_id", "orders", ["warehouse_id"], schema=SCHEMA)
    op.create_index("ix_orders_status", "orders", ["status"], schema=SCHEMA)
    op.create_index("ix_orders_created_at", "orders", ["created_at"], schema=SCHEMA)

    op.create_table(
        "order_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("variant_id", sa.String(length=36), nullable=True),
        sa.Column("product_name", sa.String(length=300), nullable=False),
        sa.Column("sku", sa.String(length=80), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], [f"{SCHEMA}.product_variants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"], schema=SCHEMA)
    op.create_index("ix_order_items_variant_id", "order_items", ["variant_id"], schema=SCHEMA)

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="mercadopago"),
        sa.Column("provider_payment_id", sa.String(length=120), nullable=True),
        sa.Column("method", sa.String(length=60), nullable=True),
        sa.Column("status", payment_status, nullable=False, server_default="pending"),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("platform_fee", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seller_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="COP"),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_payments_order_id", "payments", ["order_id"], schema=SCHEMA)
    op.create_index("ix_payments_provider_payment_id", "payments", ["provider_payment_id"], schema=SCHEMA)
    op.create_index("ix_payments_status", "payments", ["status"], schema=SCHEMA)

    op.create_table(
        "shipments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("carrier", sa.String(length=120), nullable=True),
        sa.Column("tracking_number", sa.String(length=120), nullable=True),
        sa.Column("tracking_url", sa.String(length=500), nullable=True),
        sa.Column("cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", shipment_status, nullable=False, server_default="pending"),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_shipments_order_id", "shipments", ["order_id"], schema=SCHEMA)
    op.create_index("ix_shipments_tracking_number", "shipments", ["tracking_number"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("shipments", schema=SCHEMA)
    op.drop_table("payments", schema=SCHEMA)
    op.drop_table("order_items", schema=SCHEMA)
    op.drop_table("orders", schema=SCHEMA)
    op.drop_table("addresses", schema=SCHEMA)
    op.drop_column("users", "active", schema=SCHEMA)

    sa.Enum(name="shipment_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sale_channel", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="order_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)
