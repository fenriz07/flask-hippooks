"""Move drinks column to menu

Revision ID: 32204f641d38
Revises: 1c4cde6a40ec
Create Date: 2015-09-02 22:52:09.248183

"""

# revision identifiers, used by Alembic.
revision = '32204f641d38'
down_revision = '1c4cde6a40ec'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    db.session.execute("""
        UPDATE Class_description
        SET menu=CONCAT(menu, '\nTo taste: ', drinks)
    """)
    op.drop_column("Class_description", "drinks")


def downgrade():
    pass
