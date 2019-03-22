"""Add mailing info for gift certificate orders

Revision ID: 1482e7378ad7
Revises: f59eaec6560
Create Date: 2015-10-15 19:02:46.347871

"""

# revision identifiers, used by Alembic.
revision = '1482e7378ad7'
down_revision = 'f59eaec6560'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        "gift_certificate_order",
        sa.Column("name_on_envelope", sa.String(255))
    )
    op.add_column(
        "gift_certificate_order",
        sa.Column("street_address", sa.String(255))
    )
    op.add_column(
        "gift_certificate_order",
        sa.Column("city", sa.String(100))
    )
    op.add_column(
        "gift_certificate_order",
        sa.Column("state", sa.String(2))
    )
    op.add_column(
        "gift_certificate_order",
        sa.Column("zip_code", sa.String(10))
    )


def downgrade():
    op.drop_column("gift_certificate_order", "name_on_envelope")
    op.drop_column("gift_certificate_order", "street_address")
    op.drop_column("gift_certificate_order", "city")
    op.drop_column("gift_certificate_order", "state")
    op.drop_column("gift_certificate_order", "zip_code")
