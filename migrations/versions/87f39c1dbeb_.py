"""Adds a duration to Campuses

Revision ID: 87f39c1dbeb
Revises: 32214f641d38
Create Date: 2015-09-11 23:16:32.628936

"""

# revision identifiers, used by Alembic.
revision = '87f39c1dbeb'
down_revision = '32214f641d38'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.add_column("Class_campus",
                  sa.Column("duration", sa.Integer))
    db.session.execute("UPDATE Class_campus SET duration=3")


def downgrade():
    op.drop_column("Class_campus", "duration")
