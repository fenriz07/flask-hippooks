"""Add order code to ScheduleOrder

Revision ID: 324a4d25940d
Revises: 4e2abc6d63e6
Create Date: 2015-10-22 21:08:02.059776

"""

# revision identifiers, used by Alembic.
revision = '324a4d25940d'
down_revision = '4e2abc6d63e6'

from alembic import op
from base64 import b32encode
from hipcooks import db
import sqlalchemy as sa
from os import urandom


def upgrade():
    op.add_column(
        "schedule_order",
        sa.Column(
            "code",
            sa.String(10),
            index=True,
            unique=True,
        )
    )
    schedule_order = sa.sql.table(
        "schedule_order",
        sa.Column("order_id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(10))
    )
    db.session.begin()
    try:
        for (id,) in db.session.query(schedule_order.c.order_id):
            db.session.execute(
                schedule_order.update()
                    .where(schedule_order.c.order_id == id)
                    .values({
                        "code": b32encode(urandom(5))[:7],
                    })
            )
    except:
        db.session.rollback()
        raise
    db.session.commit()
    op.alter_column(
        "schedule_order",
        "code",
        existing_type=sa.String(10),
        nullable=False,
    )


def downgrade():
    op.drop_column("schedule_order", "code")
