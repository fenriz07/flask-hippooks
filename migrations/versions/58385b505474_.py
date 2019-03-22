"""Adds Setup tables

Revision ID: 58385b505474
Revises: 378673b0ec65
Create Date: 2015-09-18 16:40:36.920688

"""

# revision identifiers, used by Alembic.
revision = '58385b505474'
down_revision = '378673b0ec65'

from alembic import op
import sqlalchemy as sa


def upgrade():
    Setup = op.create_table(
        "setup",
        sa.Column(
            "id", sa.Integer,
            sa.ForeignKey("Class_description.description_id"),
            primary_key=True
        ),
        sa.Column("pre_prep", sa.Text),
        sa.Column("prep", sa.Text),
        sa.Column("setup", sa.Text),
        sa.Column("class_intro", sa.Text),
        sa.Column("menu_intro", sa.Text),
        mysql_default_charset=u'utf8mb4',
        mysql_engine="InnoDB",
    )
    SetupRound = op.create_table(
        "setup_round",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("setup_id", sa.Integer, sa.ForeignKey(Setup.c.id)),
        sa.Column("round_number", sa.Integer),
        sa.Column("round_intro", sa.Text),
        mysql_default_charset=u'utf8mb4',
        mysql_engine="InnoDB",
    )
    op.create_table(
        "setup_round_point",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("round_id", sa.Integer, sa.ForeignKey(SetupRound.c.id)),
        sa.Column("teaching_point", sa.Text),
        sa.Column("action_point", sa.Text),
        mysql_default_charset=u'utf8mb4',
        mysql_engine="InnoDB",
    )


def downgrade():
    op.drop_table("setup_round_point")
    op.drop_table("setup_round")
    op.drop_table("setup")
