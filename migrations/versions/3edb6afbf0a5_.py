"""Adds unique constraint to subscriber emails

Revision ID: 3edb6afbf0a5
Revises: 2bc59024f9e9
Create Date: 2015-12-03 21:17:34.434676

"""

# revision identifiers, used by Alembic.
revision = '3edb6afbf0a5'
down_revision = '2bc59024f9e9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index(
        "ix_Newsletter_subscriber_email",
        "Newsletter_subscriber",
        ["email"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_Newsletter_subscriber_email",
        "Newsletter_subscriber",
    )
