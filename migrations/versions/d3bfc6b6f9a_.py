"""empty message

Revision ID: d3bfc6b6f9a
Revises: 1203b0fa5802
Create Date: 2016-01-19 00:48:09.210086

"""

# revision identifiers, used by Alembic.
revision = 'd3bfc6b6f9a'
down_revision = '1203b0fa5802'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('purchase_type', sa.String(length=20), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'purchase_type')
    ### end Alembic commands ###