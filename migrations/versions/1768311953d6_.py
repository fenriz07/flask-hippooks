"""Add permission sets from Kyrsten's CSV

Revision ID: 1768311953d6
Revises: 1572308bc3d2
Create Date: 2016-02-09 02:31:13.489301

"""

# revision identifiers, used by Alembic.
revision = '1768311953d6'
down_revision = '1572308bc3d2'

from alembic import op
import sqlalchemy as sa
from hipcooks import db, models
from logging import info

def upgrade():
    try:
        op.drop_table("permission")
        op.drop_table("permission_type")
    except sa.exc.OperationalError as e:
        info("Permissions don't already exist - %s", e)
    permission_type = op.create_table(
        "permission_type",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(30), index=True),
        sa.Column("name", sa.String(255)),
        mysql_engine="InnoDB",
        mysql_default_charset="utf8mb4",
    )
    op.create_table(
        "permission",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("auth_user.id")),
        sa.Column("campus_id", sa.Integer,
                  sa.ForeignKey("Class_campus.campus_id")),
        sa.Column("permission_type_id", sa.Integer,
                  sa.ForeignKey("permission_type.id")),
        sa.Column("can_view", sa.Boolean, default=False),
        sa.Column("can_update", sa.Boolean, default=False),
        mysql_engine="InnoDB",
        mysql_default_charset="utf8mb4",
    )
    op.bulk_insert(permission_type, [
        {"key": "schedule", "type": "Class Schedules"},
        {"key": "schedule_report", "type": "Class Report"},
        {"key": "class", "type": "Class List"},
        {"key": "class_recipes", "type": "Recipes"},
        {"key": "class_setups", "type": "Setups"},
        {"key": "class_shoplists", "type": "Shoplists for Classes"},
        {"key": "shoplist", "type": "Shoplists for Shopping"},
        {"key": "shoplist_generate",
         "type": "Shoplist - Create New and Check List"},
        {"key": "shoplist_shop", "type": "Shoplist - Go Shopping"},
        {"key": "shoplist_check", "type": "Shoplist - Check in Shop"},
        {"key": "shoplist_delete", "type": "Shoplist - Delete"},
        {"key": "reports", "type": "Reports"},
        {"key": "subscriber_list", "type": "Newsletter Subscribers"},
        {"key": "content", "type": "Web Texts (Content)"},
        {"key": "make_sale", "type": "Make a Sale"},
        {"key": "product", "type": "Tinker in Store (Products)"},
        {"key": "campus", "type": "Studios"},
        {"key": "staff", "type": "Staff"},
        {"key": "giftcertificate", "type": "Gift Certificates"},
    ])


def downgrade():
    pass
