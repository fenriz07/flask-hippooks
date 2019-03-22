"""empty message

Revision ID: 2eb7b5bbf022
Revises: 261441defc5e
Create Date: 2016-05-12 13:34:27.128732

"""

# revision identifiers, used by Alembic.
revision = '2eb7b5bbf022'
down_revision = '261441defc5e'

# standard imports
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# custom imports
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker, Session as BaseSession
from flask_sqlalchemy import _SessionSignalEvents
from hipcooks import models

try:
    event.remove(BaseSession, 'before_commit', _SessionSignalEvents.session_signal_before_commit)
    event.remove(BaseSession, 'after_commit', _SessionSignalEvents.session_signal_after_commit)
    event.remove(BaseSession, 'after_rollback', _SessionSignalEvents.session_signal_after_rollback)
except:
    pass

Session = sessionmaker()


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Class_assistant', sa.Column('classes', sa.Integer(), nullable=True))
    op.add_column('Class_assistant', sa.Column('credits', sa.Integer(), nullable=True))
    ### end Alembic commands ###

    bind = op.get_bind()
    session = Session(bind=bind)

    for assistant in session.query(models.Assistant).all():
        assistant.credits = assistant.gift_certificate_credits
        assistant.classes = len(assistant.schedule_classes)
        session.add(assistant)

    session.commit()


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Class_assistant', 'credits')
    op.drop_column('Class_assistant', 'classes')
    ### end Alembic commands ###