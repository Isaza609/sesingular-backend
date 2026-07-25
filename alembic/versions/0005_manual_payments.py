"""payout accounts, manual payment receipt fields, in_review payment status

Revision ID: 0005_manual_payments
Revises: 0004_frontend_fields
Create Date: 2026-07-25

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_manual_payments"
down_revision: Union[str, None] = "0004_frontend_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    # Nuevo estado de pago: comprobante subido, esperando revisión del vendedor.
    op.execute(f"ALTER TYPE \"{SCHEMA}\".payment_status ADD VALUE IF NOT EXISTS 'in_review' AFTER 'pending'")

    payout_account_type = postgresql.ENUM(
        "bank", "bre_b", name="payout_account_type", schema=SCHEMA, create_type=False
    )
    postgresql.ENUM("bank", "bre_b", name="payout_account_type", schema=SCHEMA).create(
        op.get_bind(), checkfirst=True
    )

    # Cuentas de cobro manual del vendedor (RF-PAGO-01).
    op.create_table(
        "payout_accounts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("type", payout_account_type, nullable=False, server_default="bank"),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("bank_name", sa.String(length=120), nullable=True),
        sa.Column("account_type", sa.String(length=40), nullable=True),
        sa.Column("account_number", sa.String(length=60), nullable=True),
        sa.Column("breb_key", sa.String(length=120), nullable=True),
        sa.Column("holder_name", sa.String(length=200), nullable=False),
        sa.Column("holder_document", sa.String(length=40), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], [f"{SCHEMA}.stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index("ix_payout_accounts_store_id", "payout_accounts", ["store_id"], schema=SCHEMA)

    # Rastro del pago manual sobre el pago existente (RF-PAGO-03/05).
    op.add_column("payments", sa.Column("payout_account_id", sa.String(length=36), nullable=True), schema=SCHEMA)
    op.add_column("payments", sa.Column("receipt_path", sa.String(length=500), nullable=True), schema=SCHEMA)
    op.add_column("payments", sa.Column("receipt_uploaded_at", sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column("payments", sa.Column("received_amount", sa.Integer(), nullable=True), schema=SCHEMA)
    op.add_column("payments", sa.Column("review_note", sa.Text(), nullable=True), schema=SCHEMA)
    op.add_column("payments", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column("payments", sa.Column("reviewed_by", sa.String(length=36), nullable=True), schema=SCHEMA)
    op.create_foreign_key(
        "fk_payments_payout_account",
        "payments",
        "payout_accounts",
        ["payout_account_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="SET NULL",
    )
    op.create_index("ix_payments_payout_account_id", "payments", ["payout_account_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_payments_payout_account_id", table_name="payments", schema=SCHEMA)
    op.drop_constraint("fk_payments_payout_account", "payments", type_="foreignkey", schema=SCHEMA)
    for column in (
        "reviewed_by",
        "reviewed_at",
        "review_note",
        "received_amount",
        "receipt_uploaded_at",
        "receipt_path",
        "payout_account_id",
    ):
        op.drop_column("payments", column, schema=SCHEMA)

    op.drop_table("payout_accounts", schema=SCHEMA)
    sa.Enum(name="payout_account_type", schema=SCHEMA).drop(op.get_bind(), checkfirst=True)

    # Postgres no permite quitar un valor de un enum: se recrea el tipo sin 'in_review'.
    op.execute(f"UPDATE \"{SCHEMA}\".payments SET status = 'pending' WHERE status = 'in_review'")
    op.execute(f"ALTER TYPE \"{SCHEMA}\".payment_status RENAME TO payment_status_old")
    postgresql.ENUM(
        "pending", "paid", "rejected", "refunded", name="payment_status", schema=SCHEMA
    ).create(op.get_bind(), checkfirst=False)
    op.execute(
        f"ALTER TABLE \"{SCHEMA}\".payments ALTER COLUMN status TYPE \"{SCHEMA}\".payment_status "
        f"USING status::text::\"{SCHEMA}\".payment_status"
    )
    op.execute(f"DROP TYPE \"{SCHEMA}\".payment_status_old")
