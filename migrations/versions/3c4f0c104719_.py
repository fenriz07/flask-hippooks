"""empty message

Revision ID: 3c4f0c104719
Revises: 31be75e1fa29
Create Date: 2016-06-13 14:56:08.641671

"""

# revision identifiers, used by Alembic.
revision = '3c4f0c104719'
down_revision = '31be75e1fa29'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('resources_kitchen', sa.Column('manufacturer', sa.String(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('resources_kitchen', 'manufacturer')
    ### end Alembic commands ###