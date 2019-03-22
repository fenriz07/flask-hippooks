"""empty message

Revision ID: 3dec851f843
Revises: 58f3751e0355
Create Date: 2015-06-01 21:27:06.215619

"""

# revision identifiers, used by Alembic.
revision = '3dec851f843'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column("auth_user", "last_login")
    op.alter_column("auth_user", "username", type_=sa.String(255))
    op.alter_column("auth_user", "first_name", type_=sa.String(255))
    op.alter_column("auth_user", "last_name", type_=sa.String(255))


def downgrade():
    pass
