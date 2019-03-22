"""Adds table for the forgotten passwords

Revision ID: 593724f3065b
Revises: 37461b6e931
Create Date: 2016-01-29 00:22:54.108505

"""

# revision identifiers, used by Alembic.
revision = '593724f3065b'
down_revision = '37461b6e931'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "forgot_password_links",
        sa.Column("code", sa.String(255), primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("auth_user.id")),
        sa.Column("expires", sa.DateTime),
        sa.Column("used", sa.Boolean, server_default=sa.literal(False)),
    )


def downgrade():
    op.drop_table("forgot_password_links")
