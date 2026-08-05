"""product variant images for Epica 04

Revision ID: 0008_product_variant_images
Revises: 0007_store_public_profile
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_product_variant_images"
down_revision: Union[str, None] = "0007_store_public_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "marketplace"


def upgrade() -> None:
    op.add_column(
        "product_images",
        sa.Column("variant_id", sa.String(length=36), nullable=True),
        schema=SCHEMA,
    )
    op.create_foreign_key(
        "fk_product_images_variant_id_product_variants",
        "product_images",
        "product_variants",
        ["variant_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_product_images_variant_id",
        "product_images",
        ["variant_id"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_product_images_variant_id", table_name="product_images", schema=SCHEMA)
    op.drop_constraint(
        "fk_product_images_variant_id_product_variants",
        "product_images",
        schema=SCHEMA,
        type_="foreignkey",
    )
    op.drop_column("product_images", "variant_id", schema=SCHEMA)
