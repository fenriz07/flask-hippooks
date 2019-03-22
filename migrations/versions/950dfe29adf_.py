"""Add model for items in the "What's in our Kitchen" page

Revision ID: 950dfe29adf
Revises: 3d868350c087
Create Date: 2016-02-03 16:08:45.395682

"""

# revision identifiers, used by Alembic.
revision = '950dfe29adf'
down_revision = '3d868350c087'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "resources_kitchen",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category", sa.String(31)),
        sa.Column("picture", sa.String(255)),
        sa.Column("link", sa.String(255)),
        sa.Column("name", sa.String(255)),
        sa.Column("order", sa.Integer),
    )


def downgrade():
    op.drop_table("resources_kitchen")
