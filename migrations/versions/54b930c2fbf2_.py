"""empty message

Revision ID: 54b930c2fbf2
Revises: 1925c010afff
Create Date: 2015-12-08 01:44:48.538662

"""

# revision identifiers, used by Alembic.
revision = '54b930c2fbf2'
down_revision = '1925c010afff'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shopping_list_instance', sa.Column('name', sa.String(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('shopping_list_instance', 'name')
    ### end Alembic commands ###