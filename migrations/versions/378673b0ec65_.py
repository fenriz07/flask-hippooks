"""Add quantity to join-table between shopping list instance items and real shopping list items

Revision ID: 378673b0ec65
Revises: 168fc7740caa
Create Date: 2015-09-17 06:45:29.362714

"""

# revision identifiers, used by Alembic.
revision = '378673b0ec65'
down_revision = '168fc7740caa'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column("shopping_list_instance_item_map", sa.Column("quantity", sa.Integer(), nullable=False, default=1))


def downgrade():
    pass
