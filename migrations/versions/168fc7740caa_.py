"""empty message

Revision ID: 168fc7740caa
Revises: 100f50116262
Create Date: 2015-09-17 01:41:16.177076

"""

# revision identifiers, used by Alembic.
revision = '168fc7740caa'
down_revision = '100f50116262'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.create_table('shopping_list_instance',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('user_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('created', mysql.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], [u'auth_user.id']),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )

    op.create_table('shopping_list_instance_item',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('shopping_list_instance_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('campus_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('number', mysql.VARCHAR(length=5), nullable=True),
    sa.Column('unit', mysql.VARCHAR(length=25), nullable=True),
    sa.Column('name', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('market', mysql.VARCHAR(length=255), nullable=True),
    sa.Column('notes', mysql.VARCHAR(length=255), nullable=True),
    sa.ForeignKeyConstraint(['shopping_list_instance_id'], [u'shopping_list_instance.id']),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )

    op.create_table('shopping_list_instance_item_map',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('shopping_list_item_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.Column('shopping_list_instance_item_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.ForeignKeyConstraint(['shopping_list_instance_item_id'], [u'shopping_list_instance_item.id']),
    sa.ForeignKeyConstraint(['shopping_list_item_id'], [u'shopping_list_item.id']),
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )

def downgrade():
    pass
