"""Adds a tab name field for studios

Revision ID: 16c4968add6b
Revises: 4a4ff39e9362
Create Date: 2015-12-14 18:05:49.252879

"""

# revision identifiers, used by Alembic.
revision = '16c4968add6b'
down_revision = '4a4ff39e9362'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.add_column("Class_campus", sa.Column("tab_name", sa.String(255)))
    campus = sa.sql.table(
        "Class_campus",
        sa.Column("campus_id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255)),
        sa.Column("tab_name", sa.String(255)),
    )
    db.session.execute(campus.update().values(tab_name=campus.c.name))
    db.session.execute(
        campus.update()
              .where(campus.c.campus_id == sa.bindparam("id"))
              .values(tab_name=sa.bindparam("tab_name")), [
                    {"id": 1, "tab_name": "East LA"},
                    {"id": 2, "tab_name": "West LA"},
              ]
    )


def downgrade():
    op.drop_column("Class_campus", "tab_name")
