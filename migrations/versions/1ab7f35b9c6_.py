"""Add active column for newsletter subscribers, enabling soft-delete

Revision ID: 1ab7f35b9c6
Revises: 3ddd7f414e92
Create Date: 2015-10-13 16:28:16.288109

"""

# revision identifiers, used by Alembic.
revision = '1ab7f35b9c6'
down_revision = '3ddd7f414e92'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column("Newsletter_subscriber",
                  sa.Column("active", sa.Boolean, server_default="1"))

def downgrade():
    pass
