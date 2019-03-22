"""Rerun 53944822f490

Revision ID: 58c33439489e
Revises: 268945a444ed
Create Date: 2016-01-19 22:42:57.140964

"""

# revision identifiers, used by Alembic.
revision = '58c33439489e'
down_revision = '268945a444ed'

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
        op.add_column('shopping_list_instance_item', sa.Column('checked_in', sa.Boolean(), nullable=True))
    except sa.exc.OperationalError:
        pass


def downgrade():
    pass
