"""Add missing schedule_order table

Revision ID: 150a70fbe43b
Revises: 2acf9586f06f
Create Date: 2015-10-14 21:18:54.479255

"""

# revision identifiers, used by Alembic.
revision = '150a70fbe43b'
down_revision = '2acf9586f06f'

from alembic import op
import sqlalchemy as sa
import logging


def upgrade():
    try:
        op.create_table(
            "schedule_order",
            sa.Column("order_id", sa.Integer, primary_key=True),
            sa.Column(
                "schedule_id",
                sa.Integer,
                sa.ForeignKey("Class_schedule.schedule_id"),
                nullable=False
            ),
            sa.Column(
                "user_id",
                sa.Integer,
                sa.ForeignKey("auth_user.id"),
                nullable=False
            ),
            sa.Column(
                "purchase_id",
                sa.Integer,
                sa.ForeignKey("purchase.id"),
                nullable=True
            ),
            sa.Column(
                "comments", sa.String(255), server_default="", nullable=False),
            sa.Column("unit_price", sa.Integer, nullable=False),
            sa.Column(
                "cancelled", sa.Boolean, server_default="0", nullable=False),
        )
    except sa.exc.OperationalError:
        logging.warn("Skipping table schedule_order since it already exists")


def downgrade():
    op.drop_table("schedule_order")
