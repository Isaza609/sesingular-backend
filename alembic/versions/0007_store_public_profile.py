"""store public profile fields for Epica 02

Revision ID: 0007_store_public_profile
Revises: 0006_user_password_state
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_store_public_profile"
down_revision: Union[str, None] = "0006_user_password_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    op.add_column(
        "stores",
        sa.Column("whatsapp_phone", sa.String(length=40), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "stores",
        sa.Column(
            "social_links",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("stores", "social_links", schema=SCHEMA)
    op.drop_column("stores", "whatsapp_phone", schema=SCHEMA)
