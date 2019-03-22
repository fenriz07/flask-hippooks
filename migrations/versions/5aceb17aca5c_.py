"""Make schedule_order.user_id nullable

Revision ID: 5aceb17aca5c
Revises: 469f96f86ba9
Create Date: 2016-02-17 14:24:30.788103

"""

# revision identifiers, used by Alembic.
revision = '5aceb17aca5c'
down_revision = '469f96f86ba9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        "schedule_order", "user_id", nullable=True, existing_type=sa.Integer)


def downgrade():
    pass
