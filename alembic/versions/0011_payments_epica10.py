"""epica 10 pagos: estado incomplete, historial payment_events, agreement_note

Revision ID: 0011_payments_epica10
Revises: 0010_checkout_groups
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_payments_epica10"
down_revision: Union[str, None] = "0010_checkout_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    # HU-PAG-07: nuevo estado pago_incompleto. ALTER TYPE ... ADD VALUE no puede
    # correr dentro de un bloque transaccional en Postgres; se aisla en autocommit.
    with op.get_context().autocommit_block():
        op.execute(
            f"ALTER TYPE \"{SCHEMA}\".payment_status ADD VALUE IF NOT EXISTS 'incomplete' AFTER 'in_review'"
        )

    # HU-PAG-07: constancia del acuerdo cuando el comprador pagó de más.
    op.add_column("payments", sa.Column("agreement_note", sa.Text(), nullable=True), schema=SCHEMA)

    # HU-PAG-09: bitácora de estados de la transacción.
    op.create_table(
        "payment_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("payment_id", sa.String(length=36), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("received_amount", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], [f"{SCHEMA}.payments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_payment_events_payment_id", "payment_events", ["payment_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_payment_events_payment_id", table_name="payment_events", schema=SCHEMA)
    op.drop_table("payment_events", schema=SCHEMA)
    op.drop_column("payments", "agreement_note", schema=SCHEMA)

    # Postgres no permite quitar un valor de un enum: se recrea el tipo sin 'incomplete'.
    op.execute(f"UPDATE \"{SCHEMA}\".payments SET status = 'pending' WHERE status = 'incomplete'")
    op.execute(f"ALTER TYPE \"{SCHEMA}\".payment_status RENAME TO payment_status_old")
    op.execute(
        f"CREATE TYPE \"{SCHEMA}\".payment_status AS ENUM "
        "('pending', 'in_review', 'paid', 'rejected', 'refunded')"
    )
    op.execute(
        f"ALTER TABLE \"{SCHEMA}\".payments ALTER COLUMN status TYPE \"{SCHEMA}\".payment_status "
        f"USING status::text::\"{SCHEMA}\".payment_status"
    )
    op.execute(f"DROP TYPE \"{SCHEMA}\".payment_status_old")
