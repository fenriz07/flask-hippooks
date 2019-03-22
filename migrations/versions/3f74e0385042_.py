"""Adds an order column to the studios

Revision ID: 3f74e0385042
Revises: 3edb6afbf0a5
Create Date: 2015-12-03 22:03:47.024822

"""

# revision identifiers, used by Alembic.
revision = '3f74e0385042'
down_revision = '3edb6afbf0a5'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.add_column("Class_campus", sa.Column("order", sa.Integer))
    studio = sa.sql.table(
        "Class_campus",
        sa.Column("campus_id", sa.Integer, primary_key=True),
        sa.Column("order", sa.Integer),
    )
    campus_update = studio.update()\
        .where(studio.c.campus_id == sa.bindparam("id"))\
        .values(order=sa.bindparam("order"))
    db.session.execute(campus_update, [
        {"id": 2, "order": 10},
        {"id": 1, "order": 20},
        {"id": 6, "order": 30},
        {"id": 5, "order": 40},
        {"id": 4, "order": 50},
        {"id": 3, "order": 60},
    ])


def downgrade():
    op.drop_column("Class_campus", "order")
