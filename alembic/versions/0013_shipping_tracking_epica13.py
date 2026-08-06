"""epica 13 envios: shipment tracking timeline, shipment note, product shipping override

Revision ID: 0013_shipping_tracking_epica13
Revises: 0012_invoices_orders_epica11_12
Create Date: 2026-08-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_shipping_tracking_epica13"
down_revision: Union[str, None] = "0012_invoices_orders_epica11_12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    # HU-ENV-05: estado de seguimiento y nota libre en el envio.
    op.add_column("shipments", sa.Column("tracking_status", sa.String(length=30), nullable=True), schema=SCHEMA)
    op.add_column("shipments", sa.Column("note", sa.Text(), nullable=True), schema=SCHEMA)

    # HU-ENV-01: override de modalidad de envio por producto.
    op.add_column("products", sa.Column("shipping_mode", sa.String(length=20), nullable=True), schema=SCHEMA)

    # HU-ENV-05: linea de tiempo del envio.
    op.create_table(
        "shipment_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("shipment_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["shipment_id"], [f"{SCHEMA}.shipments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_shipment_events_shipment_id", "shipment_events", ["shipment_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_shipment_events_shipment_id", table_name="shipment_events", schema=SCHEMA)
    op.drop_table("shipment_events", schema=SCHEMA)
    op.drop_column("products", "shipping_mode", schema=SCHEMA)
    op.drop_column("shipments", "note", schema=SCHEMA)
    op.drop_column("shipments", "tracking_status", schema=SCHEMA)
