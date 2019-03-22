"""Add color code to classes

Revision ID: 1dab34b3e817
Revises: 14108430f122
Create Date: 2015-10-27 23:48:34.862814

"""

# revision identifiers, used by Alembic.
revision = '1dab34b3e817'
down_revision = '14108430f122'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Class_description', sa.Column('color_code', sa.String(length=7), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Class_description', 'color_code')
    ### end Alembic commands ###