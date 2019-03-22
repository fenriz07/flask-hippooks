"""Adds directions field to campus

Revision ID: 4dc93c32067
Revises: 397eedc2c417
Create Date: 2015-11-11 17:55:32.726694

"""

# revision identifiers, used by Alembic.
revision = '4dc93c32067'
down_revision = '397eedc2c417'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Class_campus", sa.Column(
        "directions", sa.Text, nullable=False))
    op.add_column("Class_campus", sa.Column(
        "embed_url", sa.Text, nullable=False))


def downgrade():
    op.drop_column("Class_campus", "directions")
    op.drop_column("Class_campus", "embed_url")
