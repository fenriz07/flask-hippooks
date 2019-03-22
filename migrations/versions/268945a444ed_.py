"""rerun 433267c1db40

Revision ID: 268945a444ed
Revises: c78d6e322ae
Create Date: 2016-01-19 22:38:37.123253

"""

# revision identifiers, used by Alembic.
revision = '268945a444ed'
down_revision = 'c78d6e322ae'

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
        op.add_column('shopping_list_instance_item', sa.Column('got_it', sa.Boolean(), nullable=True))
    except sa.exc.OperationalError:
        pass


def downgrade():
    pass
