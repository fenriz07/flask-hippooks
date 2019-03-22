"""Recreate market resources table

Revision ID: 3d868350c087
Revises: 3d3b3f2ec107
Create Date: 2016-02-03 10:48:40.528141

"""

# revision identifiers, used by Alembic.
revision = '3d868350c087'
down_revision = '3d3b3f2ec107'

from alembic import op
from collections import namedtuple
import csv
import sqlalchemy as sa
from hipcooks import db


market_row = namedtuple("market_row", (
    "number",
    "campus_id",
    "name",
    "address_1",
    "address_2",
    "description",
    "type_1",
    "type_2",
    "type_3",
))


def upgrade():
    op.drop_table("resources_market")
    resources_market = op.create_table(
        "resources_market",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campus_id", sa.Integer,
                  sa.ForeignKey("Class_campus.campus_id")),
        sa.Column("name", sa.String(255)),
        sa.Column("address_1", sa.String(512)),
        sa.Column("address_2", sa.String(512)),
        sa.Column("description", sa.String(1024)),
        sa.Column("type_1", sa.String(1)),
        sa.Column("type_2", sa.String(1)),
        sa.Column("type_3", sa.String(1)),
        mysql_engine="InnoDB",
        mysql_default_charset=u"utf8mb4"
    )
    with open("migrations/market_data.csv", "rb") as data:
        rows = (market_row(*(unicode(cell, "utf-8") for cell in row))
                for row in csv.reader(data))
        op.bulk_insert(resources_market, [row._asdict() for row in rows])


def downgrade():
    op.drop_table("resources_market")
    op.create_table(
        "resources_market",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campus_id", sa.Integer,
                  sa.ForeignKey("Class_campus.campus_id")),
        sa.Column("name", sa.String(255)),
        sa.Column("address", sa.String(1024)),
        sa.Column("description", sa.String(1024)),
        sa.Column("type_1", sa.String(1)),
        sa.Column("type_2", sa.String(1)),
        sa.Column("type_3", sa.String(1)),
    )
