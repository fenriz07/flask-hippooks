"""Adds synthetic primary key to Newsletter_subscriber

Revision ID: 235f19642cb6
Revises: 439cca6d4887
Create Date: 2015-11-18 00:46:17.166489

"""

# revision identifiers, used by Alembic.
revision = '235f19642cb6'
down_revision = '439cca6d4887'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    op.drop_constraint("email", "Newsletter_subscriber", type_="primary")
    db.session.execute("""
        ALTER TABLE Newsletter_subscriber
        ADD id INT(11) UNSIGNED NOT NULL AUTO_INCREMENT, ADD PRIMARY KEY (id)
    """)


def downgrade():
    op.drop_column("Newsletter_subscriber", "id")
    op.create_primary_key("email", "Newsletter_subscriber", ["email"])
