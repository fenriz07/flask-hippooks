"""Remove photo album dependency on class photos.

Revision ID: 40ee26ae5327
Revises: 494a749ea22e
Create Date: 2015-10-30 00:41:40.856139

"""

# revision identifiers, used by Alembic.
revision = '40ee26ae5327'
down_revision = '494a749ea22e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Class_photo', 'caption',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    op.alter_column('Class_photo', 'home_page',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=True,
               existing_server_default=sa.text(u"'1'"))
    op.alter_column('Class_photo', 'order',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=True)
    op.alter_column('Class_photo', 'photo',
               existing_type=mysql.VARCHAR(length=100),
               nullable=True)
    op.drop_index('Class_photo_album_id', table_name='Class_photo')
    op.create_foreign_key(None, 'Class_photo', 'Class_description', ['for_class_id'], ['description_id'])
    op.drop_column('Class_photo', 'album_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Class_photo', sa.Column('album_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'Class_photo', type_='foreignkey')
    op.create_index('Class_photo_album_id', 'Class_photo', ['album_id'], unique=False)
    op.alter_column('Class_photo', 'photo',
               existing_type=mysql.VARCHAR(length=100),
               nullable=False)
    op.alter_column('Class_photo', 'order',
               existing_type=mysql.SMALLINT(display_width=5, unsigned=True),
               nullable=False)
    op.alter_column('Class_photo', 'home_page',
               existing_type=mysql.TINYINT(display_width=1),
               nullable=False,
               existing_server_default=sa.text(u"'1'"))
    op.alter_column('Class_photo', 'caption',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.create_table('captcha_store',
    sa.Column('index', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('challenge', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('response', mysql.VARCHAR(length=32), nullable=True),
    sa.Column('hashkey', mysql.VARCHAR(length=40), nullable=False),
    sa.Column('expiration', mysql.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('hashkey'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    op.create_table('captcha_sequence',
    sa.Column('value', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('max_value', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('value'),
    mysql_default_charset=u'latin1',
    mysql_engine=u'InnoDB'
    )
    ### end Alembic commands ###
