"""empty message

Revision ID: 2b146631fc1d
Revises: 58385b505474
Create Date: 2015-10-09 17:31:36.444220

"""

# revision identifiers, used by Alembic.
revision = '2b146631fc1d'
down_revision = '58385b505474'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column("shopping_list_item",
                  sa.Column("active", sa.Boolean))

def downgrade():
    pass
