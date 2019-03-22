"""Add recipe table

Revision ID: 28e2e3baea68
Revises: 32214f641d38
Create Date: 2015-09-11 22:07:09.080033

"""

# revision identifiers, used by Alembic.
revision = '28e2e3baea68'
down_revision = '32204f641d38'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "recipe_set",
        sa.Column("id", sa.Integer,
                  sa.ForeignKey("Class_description.description_id"),
                  primary_key=True),
        sa.Column("intro", sa.Text),
        sa.Column("last_updated", sa.DateTime),
        mysql_engine="InnoDB",
    )
    op.create_table(
        "recipe",
        sa.Column("recipe_id", sa.Integer, primary_key=True),
        sa.Column("set_id", sa.Integer, sa.ForeignKey("recipe_set.id")),
        sa.Column("title", sa.String(100)),
        sa.Column("serves", sa.String(100)),
        sa.Column("ingredients", sa.Text),
        sa.Column("instructions", sa.Text),
        sa.Column("order", sa.Integer),
        mysql_engine="InnoDB",
    )


def downgrade():
    pass
