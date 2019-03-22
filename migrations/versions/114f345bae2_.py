"""Add false as a default for GuestOrder.cancelled

Revision ID: 114f345bae2
Revises: 5aceb17aca5c
Create Date: 2016-02-18 10:06:34.212253

"""

# revision identifiers, used by Alembic.
revision = '114f345bae2'
down_revision = '5aceb17aca5c'

from alembic import op
import sqlalchemy as sa
from logging import info


def upgrade():
    try:
        op.execute("""
            UPDATE guest_order
            SET cancelled = FALSE
            WHERE cancelled IS NULL
        """)
        op.alter_column(
            "guest_order",
            "cancelled",
            existing_type=sa.Boolean,
            nullable=False,
            server_default=False,
        )
    except sa.exc.ProgrammingError as e:
        info("guest_order doesn't exist. Expected on clean VMs: %s", e)


def downgrade():
    pass
