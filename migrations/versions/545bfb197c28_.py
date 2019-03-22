"""Adds discount column to Shop_productsaleitem + makes money columns Numeric

Revision ID: 545bfb197c28
Revises: b1f7f9ca64a
Create Date: 2016-01-26 00:26:33.006947

"""

# revision identifiers, used by Alembic.
revision = '545bfb197c28'
down_revision = 'b1f7f9ca64a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        "Shop_productsaleitem",
        "total_amount",
        new_column_name="discounted_subtotal",
        type_=sa.Numeric(6, 2),
    )
    op.alter_column(
        "Shop_productsaleitem",
        "shipping",
        type_=sa.Numeric(6, 2),
    )
    op.alter_column(
        "Shop_productsaleitem",
        "tax",
        type_=sa.Numeric(6, 2),
    )


def downgrade():
    op.alter_column(
        "Shop_productsaleitem",
        "discounted_subtotal",
        new_column_name="total_amount",
        type_=sa.Float,
    )
    op.alter_column(
        "Shop_productsaleitem",
        "shipping",
        type_=sa.Float,
    )
    op.alter_column(
        "Shop_productsaleitem",
        "tax",
        type_=sa.Float,
    )
