"""Adds studio social media urls

Revision ID: 28d05411ce1b
Revises: 1dab34b3e817
Create Date: 2015-10-28 20:56:08.979735

"""

# revision identifiers, used by Alembic.
revision = '28d05411ce1b'
down_revision = '1dab34b3e817'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("Class_campus", sa.Column("facebook_url", sa.String(100)))
    op.add_column("Class_campus", sa.Column("instagram_url", sa.String(100)))
    op.add_column("Class_campus", sa.Column("google_plus_url", sa.String(100)))
    op.add_column("Class_campus", sa.Column("yelp_url", sa.String(100)))


def downgrade():
    op.drop_column("Class_campus", "facebook_url")
    op.drop_column("Class_campus", "instagram_url")
    op.drop_column("Class_campus", "google_plus_url")
    op.drop_column("Class_campus", "yelp_url")
