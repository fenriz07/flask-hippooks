"""empty message

Revision ID: 5930c16d1a8c
Revises: 18a086c0e3c
Create Date: 2016-06-03 13:26:41.071369

"""

# revision identifiers, used by Alembic.
revision = '5930c16d1a8c'
down_revision = '18a086c0e3c'

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

knife_map = {
    '0': '3',
    '1': '0',
    '2': '1',
    '3': '2',
}
inverse_knife_map = {v: k for k, v in knife_map.items()}

veggie_map = {
    '0': '7',
    '1': '0',
    '2': '1',
    '3': '2',
    '4': '3',
    '5': '4',
    '6': '5',
    '7': '6',
}
inverse_veggie_map = {v: k for k, v in veggie_map.items()}

dairy_map = {
    '0': '3',
    '1': '0',
    '2': '1',
    '3': '2',
}
inverse_dairy_map = {v: k for k, v in dairy_map.items()}

wheat_map = {
    '0': '3',
    '1': '0',
    '2': '1',
    '3': '2',
}
inverse_wheat_map = {v: k for k, v in wheat_map.items()}


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        for cls in session.query(models.Class).all():
            cls.knife_level = knife_map[cls.knife_level]
            cls.veggie_level = veggie_map[cls.veggie_level]
            cls.dairy_level = dairy_map[cls.dairy_level]
            cls.wheat_level = wheat_map[cls.wheat_level]
            session.add(cls)
        session.commit()
    except:
        session.rollback()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        for cls in session.query(models.Class).all():
            cls.knife_level = inverse_knife_map[cls.knife_level]
            cls.veggie_level = inverse_veggie_map[cls.veggie_level]
            cls.dairy_level = inverse_dairy_map[cls.dairy_level]
            cls.wheat_level = inverse_wheat_map[cls.wheat_level]
            session.add(cls)
        session.commit()
    except:
        session.rollback()
