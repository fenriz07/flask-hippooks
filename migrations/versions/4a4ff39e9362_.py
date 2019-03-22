"""Adds created_value field to GiftCertificate

Revision ID: 4a4ff39e9362
Revises: 1925c010afff
Create Date: 2015-12-08 21:12:24.343408

"""

# revision identifiers, used by Alembic.
revision = '4a4ff39e9362'
down_revision = '5aa65bc2c37b'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    certificate_use = op.create_table(
        "gift_certificate_use",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "certificate_id",
            sa.Integer,
            sa.ForeignKey("Shop_giftcertificate.certificate_id"),
            nullable=False,
        ),
        sa.Column("purchase_id", sa.Integer, sa.ForeignKey("purchase.id"),
                  nullable=True),
        sa.Column("amount", sa.Numeric(6, 2), nullable=False),
    )
    old_cert_order = sa.sql.table(
        "Shop_certificateorder",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("certificate_id", sa.ForeignKey("Shop_giftcertificate")),
        sa.Column("amount", sa.Integer),
    )
    old_class_gift_cert_orders = db.session.query(
        sa.null(),
        old_cert_order.c.certificate_id,
        sa.null(),
        old_cert_order.c.amount,
    ).all()
    db.session.execute(
        certificate_use.insert().values(old_class_gift_cert_orders))
    old_cert_purchase = sa.sql.table(
        "Shop_certificateproductsaleitem",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("certificate_id", sa.ForeignKey("Shop_giftcertificate")),
        sa.Column("amount", sa.Integer),
    )
    old_class_gift_cert_purchases = db.session.query(
        sa.null(),
        old_cert_purchase.c.certificate_id,
        sa.null(),
        old_cert_purchase.c.amount,
    ).all()
    db.session.execute(
        certificate_use.insert().values(old_class_gift_cert_purchases))


def downgrade():
    op.drop_table("gift_certificate_use")
