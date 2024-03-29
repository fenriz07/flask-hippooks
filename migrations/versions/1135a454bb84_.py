"""empty message

Revision ID: 1135a454bb84
Revises: 234b2409a954
Create Date: 2016-06-28 14:40:39.378056

"""

# revision identifiers, used by Alembic.
revision = '1135a454bb84'
down_revision = '234b2409a954'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('static_page', 'path',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.String(length=100),
               existing_nullable=True)
    op.alter_column('static_page', 'title',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=255),
               existing_nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('static_page', 'title',
               existing_type=sa.String(length=255),
               type_=mysql.VARCHAR(length=100),
               existing_nullable=True)
    op.alter_column('static_page', 'path',
               existing_type=sa.String(length=100),
               type_=mysql.VARCHAR(length=50),
               existing_nullable=True)
    ### end Alembic commands ###
