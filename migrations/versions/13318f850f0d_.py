"""Adds resource data to the the product page

Revision ID: 13318f850f0d
Revises: 585dc65df58c
Create Date: 2016-02-16 10:35:40.600592

"""

# revision identifiers, used by Alembic.
revision = '13318f850f0d'
down_revision = '585dc65df58c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        "Shop_product",
        sa.Column(
            "is_resource",
            sa.Boolean,
            nullable=False,
            server_default=sa.literal(False)
        )
    )
    op.add_column("Shop_product", sa.Column("resource_name", sa.String(255)))


def downgrade():
    op.drop_column("Shop_product", "is_resource")
    op.drop_column("Shop_product", "resource_name")
