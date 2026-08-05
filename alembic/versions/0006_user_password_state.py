"""user password state for Epica 01

Revision ID: 0006_user_password_state
Revises: 0005_manual_payments
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_user_password_state"
down_revision: Union[str, None] = "0005_manual_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        schema=SCHEMA,
    )
    op.add_column(
        "users",
        sa.Column("temporary_password_expires_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "users",
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    for column in (
        "last_login_at",
        "password_changed_at",
        "temporary_password_expires_at",
        "must_change_password",
    ):
        op.drop_column("users", column, schema=SCHEMA)
