"""Adds captcha tables

Revision ID: 1a5d8a96c3d
Revises: 38a549a5b880
Create Date: 2015-10-29 18:51:14.760106

"""

# revision identifiers, used by Alembic.
revision = '1a5d8a96c3d'
down_revision = '38a549a5b880'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "captcha_sequence",
        sa.Column("value", sa.Integer, primary_key=True),
        sa.Column("max_value", sa.Integer),
    )

    op.create_table(
        "captcha_store",
        sa.Column("index", sa.Integer, index=True),
        sa.Column("challenge", sa.String(32)),
        sa.Column("response", sa.String(32)),
        sa.Column("hashkey", sa.String(40), primary_key=True),
        sa.Column("expiration", sa.DateTime),
    )


def downgrade():
    op.drop_table("captcha_sequence")
    op.drop_table("captcha_store")
