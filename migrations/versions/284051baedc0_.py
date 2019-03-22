"""Set Shop_productinventory.quantity_stocked to 0 where it's null

Revision ID: 284051baedc0
Revises: 114f345bae2
Create Date: 2016-02-26 16:15:08.655416

"""

# revision identifiers, used by Alembic.
revision = '284051baedc0'
down_revision = '114f345bae2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""
        UPDATE Shop_productinventory
        SET quantity_stocked = 0
        WHERE quantity_stocked IS NULL
    """)


def downgrade():
    pass
