"""Adds active and name to ShoppingListInstance

Revision ID: c78d6e322ae
Revises: 12de3be7d375
Create Date: 2016-01-19 21:09:47.790694

"""

# revision identifiers, used by Alembic.
revision = 'c78d6e322ae'
down_revision = '12de3be7d375'

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
	    op.add_column("shopping_list_instance",
			  sa.Column("active", sa.Boolean,
				    server_default=sa.literal(True)))
    except sa.exc.OperationalError:
        pass
    try:
        op.add_column("shopping_list_instance", sa.Column("name", sa.String(255)))
    except sa.exc.OperationalError:
        pass


def downgrade():
    op.drop_column("shopping_list_instance", "active")
    op.drop_column("shopping_list_instance", "name")
