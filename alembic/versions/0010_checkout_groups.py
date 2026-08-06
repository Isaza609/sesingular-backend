"""checkout groups for Epica 09

Revision ID: 0010_checkout_groups
Revises: 0009_pricing_promotions
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_checkout_groups"
down_revision: Union[str, None] = "0009_pricing_promotions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    op.create_table(
        "checkout_groups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("buyer_id", sa.String(length=36), nullable=False),
        sa.Column("address_id", sa.String(length=36), nullable=True),
        sa.Column("subtotal", sa.Integer(), nullable=False),
        sa.Column("discount_total", sa.Integer(), nullable=False),
        sa.Column("extra_charge_total", sa.Integer(), nullable=False),
        sa.Column("shipping_cost", sa.Integer(), nullable=False),
        sa.Column("tax", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=60), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["address_id"], [f"{SCHEMA}.addresses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["buyer_id"], [f"{SCHEMA}.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_checkout_groups_buyer_id", "checkout_groups", ["buyer_id"], schema=SCHEMA)
    op.create_index("ix_checkout_groups_address_id", "checkout_groups", ["address_id"], schema=SCHEMA)
    op.create_index("ix_checkout_groups_created_at", "checkout_groups", ["created_at"], schema=SCHEMA)

    op.add_column("orders", sa.Column("checkout_group_id", sa.String(length=36), nullable=True), schema=SCHEMA)
    op.create_index("ix_orders_checkout_group_id", "orders", ["checkout_group_id"], schema=SCHEMA)
    op.create_foreign_key(
        "fk_orders_checkout_group_id_checkout_groups",
        "orders",
        "checkout_groups",
        ["checkout_group_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_orders_checkout_group_id_checkout_groups",
        "orders",
        schema=SCHEMA,
        type_="foreignkey",
    )
    op.drop_index("ix_orders_checkout_group_id", table_name="orders", schema=SCHEMA)
    op.drop_column("orders", "checkout_group_id", schema=SCHEMA)
    op.drop_index("ix_checkout_groups_created_at", table_name="checkout_groups", schema=SCHEMA)
    op.drop_index("ix_checkout_groups_address_id", table_name="checkout_groups", schema=SCHEMA)
    op.drop_index("ix_checkout_groups_buyer_id", table_name="checkout_groups", schema=SCHEMA)
    op.drop_table("checkout_groups", schema=SCHEMA)
