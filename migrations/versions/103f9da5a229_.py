"""Adds shopping list and shopping list item tables

Revision ID: 103f9da5a229
Revises: 87f39c1dbeb
Create Date: 2015-09-16 23:43:41.685437

"""

# revision identifiers, used by Alembic.
revision = '103f9da5a229'
down_revision = '87f39c1dbeb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ShoppingList = op.create_table(
        "shopping_list",
        sa.Column("id", sa.Integer,
                  sa.ForeignKey("Class_description.description_id"),
                  primary_key=True),
        sa.Column("check", sa.Text),
        sa.Column("last_updated", sa.DateTime),
        mysql_engine="InnoDB",
    )
    op.create_table(
        "shopping_list_item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shopping_list_id", sa.Integer,
                  sa.ForeignKey("shopping_list.id")),
        sa.Column("number", sa.String(5)),
        sa.Column("unit", sa.String(25)),
        sa.Column("name", sa.String(255)),
        mysql_engine="InnoDB",
    )


def downgrade():
    pass
