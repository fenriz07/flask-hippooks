"""empty message

Revision ID: 100f50116262
Revises: 103f9da5a229
Create Date: 2015-09-16 21:46:11.772381

"""

# revision identifiers, used by Alembic.
revision = '100f50116262'
down_revision = '103f9da5a229'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column("shopping_list_item", sa.Column("category", sa.String(10), nullable=False, default=''))
    op.add_column("shopping_list_item", sa.Column("market", sa.String(255), nullable=False, default=''))
    op.add_column("shopping_list_item", sa.Column("notes", sa.String(255), nullable=False, default=''))


def downgrade():
    pass
