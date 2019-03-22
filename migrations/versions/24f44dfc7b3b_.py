"""Add name and email to guests like with schedule orders

Revision ID: 24f44dfc7b3b
Revises: 3fb799c765a6
Create Date: 2016-04-10 06:37:07.508499

"""

# revision identifiers, used by Alembic.
revision = '24f44dfc7b3b'
down_revision = '3fb799c765a6'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('guest_order', sa.Column('email', sa.String(length=75), nullable=False))
    op.add_column('guest_order', sa.Column('name', sa.String(length=255), nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('guest_order', 'name')
    op.drop_column('guest_order', 'email')
    ### end Alembic commands ###
