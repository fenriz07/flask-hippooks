"""Add transaction table`

Revision ID: 3bc1f9a32d6a
Revises: 3e9b19c9e07c
Create Date: 2015-10-26 17:58:11.073573

"""

# revision identifiers, used by Alembic.
revision = '3bc1f9a32d6a'
down_revision = '3e9b19c9e07c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "transaction",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("purchase_id", sa.Integer, sa.ForeignKey("purchase.id"),
                  index=True),
        sa.Column("payment_method", sa.String(20)),
        sa.Column("amount", sa.Integer),
        sa.Column("first_name", sa.String(255)),
        sa.Column("last_name", sa.String(255)),
        sa.Column("card_number", sa.String(16), nullable=True),
        sa.Column("exp_month", sa.Integer, nullable=True),
        sa.Column("exp_year", sa.Integer, nullable=True),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("state", sa.CHAR(2), nullable=True),
        sa.Column("zip_code", sa.String(10), nullable=True),
        sa.Column("country", sa.CHAR(2), nullable=True),
        sa.Column("authorization_code", sa.String(6), nullable=True),
        sa.Column("remote_transaction_id", sa.String(20), nullable=True),
     )


def downgrade():
    op.drop_table("transaction")
