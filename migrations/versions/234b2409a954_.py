"""empty message

Revision ID: 234b2409a954
Revises: 30d4ffc5a7ab
Create Date: 2016-06-27 13:57:41.496922

"""

# revision identifiers, used by Alembic.
revision = '234b2409a954'
down_revision = '30d4ffc5a7ab'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Class_waitinglist', sa.Column('guest_information', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Class_waitinglist', 'guest_information')
    ### end Alembic commands ###
