"""Updates database to ensure usernames = emails for non-staff members

Revision ID: 2bb3cbe234ce
Revises: 58c33439489e
Create Date: 2016-01-19 23:12:19.139022

"""

# revision identifiers, used by Alembic.
revision = '2bb3cbe234ce'
down_revision = '58c33439489e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("""
        UPDATE auth_user
        LEFT OUTER JOIN Class_teacher
        ON id=user_id
        SET username=email
        WHERE Class_teacher.user_id is NULL and email != "";
    """)


def downgrade():
    pass
