"""Create market resources table

Revision ID: 12de3be7d375
Revises: d3bfc6b6f9a
Create Date: 2016-01-18 19:00:10.079162

"""

# revision identifiers, used by Alembic.
revision = '12de3be7d375'
down_revision = 'd3bfc6b6f9a'

from alembic import op
from collections import namedtuple
import csv
import sqlalchemy as sa
from hipcooks import db


class MarketRow(namedtuple("rowdata", (
            "number",
            "campus_id",
            "name",
            "address_1",
            "address_2",
            "description",
            "type_1",
            "type_2",
            "type_3",
        ))):
    def data(self):
        return {
            "campus_id": self.campus_id,
            "name": self.name,
            "address": "{}\n{}".format(self.address_1, self.address_2),
            "description": self.description,
            "type_1": self.type_1,
            "type_2": self.type_2,
            "type_3": self.type_3,
        }


def upgrade():
    resources_market = op.create_table(
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
    with open("migrations/market_data.csv") as data:
        rows = (MarketRow(*row) for row in csv.reader(data))
        op.bulk_insert(resources_market, [row.data() for row in rows])


def downgrade():
    op.drop_table("resources_market")
