"""Creates table for the "Specialty Ingredients" resources page

Revision ID: 1572308bc3d2
Revises: 950dfe29adf
Create Date: 2016-02-04 16:32:17.471509

"""

# revision identifiers, used by Alembic.
revision = '1572308bc3d2'
down_revision = '950dfe29adf'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "resources_ingredients",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("picture", sa.String(255)),
        sa.Column("name", sa.String(255)),
        sa.Column("description", sa.String(255)),
        sa.Column("order", sa.Integer),
    )


def downgrade():
    op.drop_table("resources_ingredients")
