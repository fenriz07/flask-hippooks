"""Add studio color

Revision ID: 303ff4ac84fd
Revises: 42f6c0f8f965
Create Date: 2015-10-26 21:51:44.673443

"""

# revision identifiers, used by Alembic.
revision = '303ff4ac84fd'
down_revision = '42f6c0f8f965'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Class_campus', sa.Column('color_code', sa.String(length=7), nullable=True))
    op.alter_column('Class_campus', 'address',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    op.alter_column('Class_campus', 'authorize_net_login',
               existing_type=mysql.VARCHAR(length=12),
               nullable=True)
    op.alter_column('Class_campus', 'authorize_net_tran_key',
               existing_type=mysql.VARCHAR(length=16),
               nullable=True)
    op.alter_column('Class_campus', 'base_cost',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=True)
    op.alter_column('Class_campus', 'city',
               existing_type=mysql.VARCHAR(length=50),
               nullable=True)
    op.alter_column('Class_campus', 'class_size',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=True)
    op.alter_column('Class_campus', 'domain',
               existing_type=mysql.VARCHAR(length=31),
               nullable=True)
    op.alter_column('Class_campus', 'email',
               existing_type=mysql.VARCHAR(length=75),
               nullable=True)
    op.alter_column('Class_campus', 'name',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    op.alter_column('Class_campus', 'phone',
               existing_type=mysql.VARCHAR(length=20),
               nullable=True)
    op.alter_column('Class_campus', 'private_class_fee',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=True)
    op.alter_column('Class_campus', 'sales_tax',
               existing_type=mysql.DECIMAL(precision=4, scale=2),
               nullable=True)
    op.alter_column('Class_campus', 'start_time',
               existing_type=mysql.TIME(),
               nullable=True)
    op.alter_column('Class_campus', 'state',
               existing_type=mysql.VARCHAR(length=2),
               nullable=True)
    op.alter_column('Class_campus', 'zipcode',
               existing_type=mysql.VARCHAR(length=10),
               nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_schedule_order_code'), table_name='schedule_order')
    op.alter_column('Class_campus', 'zipcode',
               existing_type=mysql.VARCHAR(length=10),
               nullable=False)
    op.alter_column('Class_campus', 'state',
               existing_type=mysql.VARCHAR(length=2),
               nullable=False)
    op.alter_column('Class_campus', 'start_time',
               existing_type=mysql.TIME(),
               nullable=False)
    op.alter_column('Class_campus', 'sales_tax',
               existing_type=mysql.DECIMAL(precision=4, scale=2),
               nullable=False)
    op.alter_column('Class_campus', 'private_class_fee',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=False)
    op.alter_column('Class_campus', 'phone',
               existing_type=mysql.VARCHAR(length=20),
               nullable=False)
    op.alter_column('Class_campus', 'name',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.alter_column('Class_campus', 'email',
               existing_type=mysql.VARCHAR(length=75),
               nullable=False)
    op.alter_column('Class_campus', 'domain',
               existing_type=mysql.VARCHAR(length=31),
               nullable=False)
    op.alter_column('Class_campus', 'class_size',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=False)
    op.alter_column('Class_campus', 'city',
               existing_type=mysql.VARCHAR(length=50),
               nullable=False)
    op.alter_column('Class_campus', 'base_cost',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=False)
    op.alter_column('Class_campus', 'authorize_net_tran_key',
               existing_type=mysql.VARCHAR(length=16),
               nullable=False)
    op.alter_column('Class_campus', 'authorize_net_login',
               existing_type=mysql.VARCHAR(length=12),
               nullable=False)
    op.alter_column('Class_campus', 'address',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.drop_column('Class_campus', 'color_code')
    ### end Alembic commands ###