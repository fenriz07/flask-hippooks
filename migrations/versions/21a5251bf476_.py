"""Recreate gift_certificate_use with date

Revision ID: 21a5251bf476
Revises: 16c4968add6b
Create Date: 2015-12-14 23:30:32.528237

"""

# revision identifiers, used by Alembic.
revision = '21a5251bf476'
down_revision = '16c4968add6b'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.drop_table("gift_certificate_use")
    certificate_use = op.create_table(
        "gift_certificate_use",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "campus_id",
            sa.Integer,
            sa.ForeignKey("Class_campus.campus_id"),
        ),
        sa.Column(
            "certificate_id",
            sa.Integer,
            sa.ForeignKey("Shop_giftcertificate.certificate_id"),
            nullable=False,
        ),
        sa.Column("purchase_id", sa.Integer, sa.ForeignKey("purchase.id"),
                  nullable=True),
        sa.Column("amount", sa.Numeric(6, 2), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        mysql_default_charset=u'utf8mb4',
    )

    old_class_gift_cert_orders = [
        (None, int(campus_id), int(certificate_id), None, amount, date)
        for (certificate_id, campus_id, amount, date)
        in db.session.execute("""
            SELECT S_co.certificate_id, C_s.campus_id, S_co.amount,
                DATE(S_cc.timestamp)
            FROM Shop_certificateorder AS S_co
            JOIN Shop_order AS S_o ON S_co.order_id = S_o.order_id
            JOIN Class_schedule AS C_s ON S_o.schedule_id = C_s.schedule_id
            JOIN Shop_creditcard AS S_cc ON
                S_o.creditcard_id = S_cc.creditcard_id;
        """)]
    db.session.execute(
        certificate_use.insert().values(old_class_gift_cert_orders))

    old_class_gift_cert_purchases = [
        (None, int(campus_id), int(certificate_id), None, amount, date)
        for (certificate_id, campus_id, amount, date)
        in db.session.execute("""
            SELECT S_cpsi.certificate_id, S_ps.campus_id,
                S_cpsi.amount, DATE(S_ps.date_ordered)
            FROM Shop_certificateproductsaleitem AS S_cpsi
            JOIN Shop_productsaleitem AS S_psi
                ON S_cpsi.productsaleitem_id = S_psi.id
            JOIN Shop_productsale AS S_ps ON S_psi.productsale_id = S_ps.id
        """)]
    db.session.execute(
        certificate_use.insert().values(old_class_gift_cert_purchases))


def downgrade():
    op.drop_column("gift_certificate_use", "date")
