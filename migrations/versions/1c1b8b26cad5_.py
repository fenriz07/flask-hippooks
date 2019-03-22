"""empty message

Revision ID: 1c1b8b26cad5
Revises: 324a4d25940d
Create Date: 2015-10-23 15:59:41.402515

"""

# revision identifiers, used by Alembic.
revision = '1c1b8b26cad5'
down_revision = '324a4d25940d'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.add_column("Shop_product",
                  sa.Column("order", sa.Integer, nullable=False))
    try:
        db.session.execute("""
            UPDATE Shop_product
            SET Shop_product.order = placement_row * 4 + placement_col
        """)
    except:
        op.drop_column("Shop_product", "order")
        raise
    op.drop_column("Shop_product", "placement_row")
    op.drop_column("Shop_product", "placement_col")


def downgrade():
    op.add_column("Shop_product", sa.Column("placement_row", sa.Integer))
    op.add_column("Shop_product", sa.Column("placement_col", sa.Integer))
    op.drop_column("Shop_product", "order")
