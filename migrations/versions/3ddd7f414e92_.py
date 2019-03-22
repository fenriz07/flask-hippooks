"""Create Gift Certificate Order table

Revision ID: 3ddd7f414e92
Revises: 2b146631fc1d
Create Date: 2015-10-09 23:35:19.849364

"""

# revision identifiers, used by Alembic.
revision = '3ddd7f414e92'
down_revision = '2b146631fc1d'

from alembic import op
import sqlalchemy as sa
import logging


def upgrade():
    try:
        op.create_table(
            "purchase",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("timestamp", sa.DateTime, nullable=False),
            sa.Column("ip_address", sa.CHAR(15), nullable=False),
            sa.Column("amount", sa.Integer, nullable=False),
            sa.Column("first_name", sa.String(255), nullable=False),
            sa.Column("last_name", sa.String(255), nullable=False),
            sa.Column("email", sa.String(75), nullable=False),
            sa.Column("phone", sa.String(20), nullable=True),
            sa.Column("authorization_code", sa.CHAR(6), nullable=False),
        )
    except sa.exc.OperationalError:
        logging.warn("Skipping table purchase since it already exists")
    op.create_table(
        "gift_certificate_order",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campus_id", sa.Integer,
                  sa.ForeignKey("Class_campus.campus_id"), nullable=False),
        sa.Column("purchase_id", sa.Integer, sa.ForeignKey("purchase.id"),
                  nullable=True),
        sa.Column("gift_certificate_id", sa.Integer,
                  sa.ForeignKey("Shop_giftcertificate.certificate_id"),
                  nullable=True),
        sa.Column("delivery_method", sa.Integer, nullable=False),
        sa.Column("sender_name", sa.String(100), nullable=False),
        sa.Column("sender_email", sa.String(75), nullable=False),
        sa.Column("sender_phone", sa.String(20), nullable=False),
        sa.Column("amount_to_give", sa.Integer, nullable=False),
        sa.Column("recipient_name", sa.String(100), nullable=False),
        sa.Column("recipient_email", sa.String(75), nullable=False),
        sa.Column("message", sa.Text),
        mysql_default_charset=u'utf8mb4',
        mysql_engine="InnoDB",
    )


def downgrade():
    op.drop_table("gift_certificate_order")
