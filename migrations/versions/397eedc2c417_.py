"""Adds phone number fields to users

Revision ID: 397eedc2c417
Revises: 40ee26ae5327
Create Date: 2015-11-09 21:25:58.074437

"""

# revision identifiers, used by Alembic.
revision = '397eedc2c417'
down_revision = '40ee26ae5327'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("auth_user", sa.Column(
        "phone",
        sa.String(50),
        nullable=False,
        server_default="",
    ))


def downgrade():
    op.drop_column("auth_user", "phone")
