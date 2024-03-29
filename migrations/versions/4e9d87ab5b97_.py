"""Add sales comment and rating section to class report

Revision ID: 4e9d87ab5b97
Revises: 593724f3065b
Create Date: 2016-01-29 06:37:53.482372

"""

# revision identifiers, used by Alembic.
revision = '4e9d87ab5b97'
down_revision = '593724f3065b'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('class_report', sa.Column('sales_comments', sa.Text(), nullable=True))
    op.add_column('class_report', sa.Column('sales_rating', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('class_report', 'sales_rating')
    op.drop_column('class_report', 'sales_comments')
    ### end Alembic commands ###
