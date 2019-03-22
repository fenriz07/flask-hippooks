"""empty message

Revision ID: 3316b850d631
Revises: 53358d10ac88
Create Date: 2015-10-14 01:17:22.548432

"""

# revision identifiers, used by Alembic.
revision = '3316b850d631'
down_revision = '53358d10ac88'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('class_report', sa.Column('attendance_rating', sa.Integer(), nullable=True))
    op.add_column('extra_person', sa.Column('order_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'extra_person', 'schedule_order', ['order_id'], ['order_id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'extra_person', type_='foreignkey')
    op.drop_column('extra_person', 'order_id')
    op.drop_column('class_report', 'attendance_rating')
    ### end Alembic commands ###