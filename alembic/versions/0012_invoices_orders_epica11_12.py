"""epica 11-12: invoices, order assignment/cancel fields, store fiscal data

Revision ID: 0012_invoices_orders_epica11_12
Revises: 0011_payments_epica10
Create Date: 2026-08-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_invoices_orders_epica11_12"
down_revision: Union[str, None] = "0011_payments_epica10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    # HU-FAC-02: datos fiscales de la tienda.
    op.add_column("stores", sa.Column("legal_name", sa.String(length=200), nullable=True), schema=SCHEMA)
    op.add_column("stores", sa.Column("tax_id", sa.String(length=40), nullable=True), schema=SCHEMA)
    op.add_column("stores", sa.Column("fiscal_address", sa.String(length=300), nullable=True), schema=SCHEMA)

    # HU-PED-04 / HU-PED-05: motivo de anulacion y responsable del pedido.
    op.add_column("orders", sa.Column("assignee_id", sa.String(length=36), nullable=True), schema=SCHEMA)
    op.add_column("orders", sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column("orders", sa.Column("cancel_reason", sa.Text(), nullable=True), schema=SCHEMA)
    op.create_index("ix_orders_assignee_id", "orders", ["assignee_id"], schema=SCHEMA)
    op.create_foreign_key(
        "fk_orders_assignee_id_users",
        "orders",
        "users",
        ["assignee_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )

    # HU-PED-05: historial de reasignaciones.
    op.create_table(
        "order_assignment_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("from_user_id", sa.String(length=36), nullable=True),
        sa.Column("to_user_id", sa.String(length=36), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_order_assignment_events_order_id", "order_assignment_events", ["order_id"], schema=SCHEMA)

    # HU-FAC-01: comprobante de venta.
    invoice_status = postgresql.ENUM("issued", "cancelled", "returned", name="invoice_status", schema=SCHEMA, create_type=False)
    invoice_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("buyer_id", sa.String(length=36), nullable=True),
        sa.Column("status", invoice_status, nullable=False, server_default="issued"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="COP"),
        sa.Column("subtotal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discount_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extra_charge_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_cost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_to_convenir", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("store_fiscal", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("buyer_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("items_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("charges_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], [f"{SCHEMA}.orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["buyer_id"], [f"{SCHEMA}.users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_invoices_order_id"),
        schema=SCHEMA,
    )
    op.create_index("ix_invoices_store_id", "invoices", ["store_id"], schema=SCHEMA)
    op.create_index("ix_invoices_buyer_id", "invoices", ["buyer_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_invoices_buyer_id", table_name="invoices", schema=SCHEMA)
    op.drop_index("ix_invoices_store_id", table_name="invoices", schema=SCHEMA)
    op.drop_table("invoices", schema=SCHEMA)
    sa.Enum(name="invoice_status", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_order_assignment_events_order_id", table_name="order_assignment_events", schema=SCHEMA)
    op.drop_table("order_assignment_events", schema=SCHEMA)

    op.drop_constraint("fk_orders_assignee_id_users", "orders", type_="foreignkey", schema=SCHEMA)
    op.drop_index("ix_orders_assignee_id", table_name="orders", schema=SCHEMA)
    for column in ("cancel_reason", "assigned_at", "assignee_id"):
        op.drop_column("orders", column, schema=SCHEMA)

    for column in ("fiscal_address", "tax_id", "legal_name"):
        op.drop_column("stores", column, schema=SCHEMA)
