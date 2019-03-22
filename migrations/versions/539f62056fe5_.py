# coding=utf-8
"""Adds class landing text to the campus editor

Revision ID: 539f62056fe5
Revises: 1768311953d6
Create Date: 2016-02-09 10:52:29.546324

"""

# revision identifiers, used by Alembic.
revision = '539f62056fe5'
down_revision = '1768311953d6'

from alembic import op
import sqlalchemy as sa


campus = sa.sql.table(
    "Class_campus",
    sa.Column("class_in_session_body", sa.Text),
    sa.Column("the_skinny_body", sa.Text),
)


def upgrade():
    op.add_column("Class_campus", sa.Column("class_in_session_body", sa.Text))
    op.add_column("Class_campus", sa.Column("the_skinny_body", sa.Text))
    op.execute(campus.update().values({
        "class_in_session_body": """
            <p>Join us in our beautiful kitchen for an evening of fresh flavors and new friends.</p>
            <p>Hipcooks provides hands-on cooking classes for the novice and seasoned cook alike. Measuring implements are banned, tasting is encouraged, and your inner chef is invited to play. The best part? Every class ends with a dinner party!</p>
            <p>If you’d like to learn to cook healthy food for your family, fun menus for 30 of your closest friends, or knife skills to impress a samurai, Hipcooks shows you how to be as cool in the kitchen as you are everywhere else.</p>
        """,
        "the_skinny_body": """
            <p>Classes are ${{campus.base_cost}}, which includes fresh, organic (wherever possible) ingredients, tools and supplies, wine tasting with dinner.</p>
            <p>Classes are limited in size to allow for hands-on instruction. All skill levels welcome. (No minors, please)</p>
        """,
    }))


def downgrade():
    op.drop_column("Class_campus", "class_in_session_body")
    op.drop_column("Class_campus", "the_skinny_body")
