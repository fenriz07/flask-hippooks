"""empty message

Revision ID: c95ad012b6c
Revises: None
Create Date: 2015-05-17 01:22:07.330663

"""

# revision identifiers, used by Alembic.
revision = 'c95ad012b6c'
down_revision = '3dec851f843'

from alembic import op
import sqlalchemy as sa
from hipcooks import models, db
import datetime


def upgrade():
    op.add_column("Class_assistant", sa.Column("user_id", sa.Integer()))
    db.session.begin()
    for assistant in db.session.query(models.Assistant):
        user_id = db.session.query(models.User.id)\
                      .filter(models.User.email == assistant.email)\
                      .scalar()
        if user_id is None:
            result = db.session.execute(models.User.__table__.insert().values(
                username=assistant.email,
                password=models.User.hash_password(assistant.email),
                email=assistant.email,
                is_active=True,
                is_staff=False,
                is_superuser=False,
                date_joined=datetime.datetime.now(),
                first_name=assistant.first_name,
                last_name=assistant.last_name
            ))
            user_id = result.inserted_primary_key

        db.session.execute(models.Assistant.__table__.update().where(
            models.Assistant.id == assistant.id
        ).values(user_id=user_id))
    db.session.commit()
    op.create_foreign_key(None, "Class_assistant", "auth_user",
                          ["user_id"], ["id"])

def downgrade():
    pass
