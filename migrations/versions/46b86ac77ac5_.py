"""Add menu to RecipeSet

Revision ID: 46b86ac77ac5
Revises: 284051baedc0
Create Date: 2016-03-07 16:05:16.834176

"""

# revision identifiers, used by Alembic.
revision = '46b86ac77ac5'
down_revision = '284051baedc0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("recipe_set", sa.Column("menu", sa.Text))


def downgrade():
    op.drop_column("recipe_set", "menu")
