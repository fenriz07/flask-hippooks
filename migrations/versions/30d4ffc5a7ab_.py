"""empty message

Revision ID: 30d4ffc5a7ab
Revises: 238f06feea3e
Create Date: 2016-06-22 11:51:21.445326

"""

# revision identifiers, used by Alembic.
revision = '30d4ffc5a7ab'
down_revision = '238f06feea3e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('gift_certificate_block', sa.Column('created', sa.DateTime(), nullable=True))
    op.add_column('gift_certificate_block', sa.Column('last_updated', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('gift_certificate_block', 'last_updated')
    op.drop_column('gift_certificate_block', 'created')
    ### end Alembic commands ###
