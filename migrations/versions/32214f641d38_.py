"""Move drinks column to menu

Revision ID: 32214f641d38
Revises: 32204f641d38
Create Date: 2015-09-02 22:52:09.248183

"""

# revision identifiers, used by Alembic.
revision = '32214f641d38'
down_revision = '28e2e3baea68'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.add_column("recipe", sa.Column("intro", sa.Text()))

def downgrade():
    pass
