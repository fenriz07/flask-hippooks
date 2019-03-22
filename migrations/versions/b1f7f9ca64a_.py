"""ProductOrder date_* should be datetimes

Revision ID: b1f7f9ca64a
Revises: 2bb3cbe234ce
Create Date: 2016-01-25 19:57:59.862281

"""

# revision identifiers, used by Alembic.
revision = 'b1f7f9ca64a'
down_revision = '2bb3cbe234ce'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("Shop_productsale", "date_ordered", type_=sa.DateTime)
    op.alter_column("Shop_productsale", "date_sent", type_=sa.DateTime)


def downgrade():
    op.alter_column("Shop_productsale", "date_ordered", type_=sa.Date)
    op.alter_column("Shop_productsale", "date_sent", type_=sa.Date)
