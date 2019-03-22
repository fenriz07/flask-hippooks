"""Delete excess Assistants

Revision ID: 10f615d4d0f4
Revises: c95ad012b6c
Create Date: 2015-06-05 20:34:30.902732

"""

# revision identifiers, used by Alembic.
revision = '10f615d4d0f4'
down_revision = 'c95ad012b6c'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    db.session.execute("""CREATE TEMPORARY TABLE kept_assistants
                          SELECT assistant_id
                          FROM Class_assistant
                          GROUP BY email""")
    db.session.execute("""DELETE FROM Class_assistant
                          WHERE assistant_id NOT IN
                            (SELECT assistant_id FROM kept_assistants)""")


def downgrade():
    pass
