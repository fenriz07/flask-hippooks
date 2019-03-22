"""Adds sidebar ad as a static content item

Revision ID: 469f96f86ba9
Revises: 13318f850f0d
Create Date: 2016-02-17 10:52:34.769758

"""

# revision identifiers, used by Alembic.
revision = '469f96f86ba9'
down_revision = '13318f850f0d'

from alembic import op
import sqlalchemy as sa


CATEGORY_CONTENT = "c"
static_page = sa.sql.table(
    "static_page",
    sa.Column("path", sa.String(50), index=True, unique=True),
    sa.Column("title", sa.String(100)),
    sa.Column("body", sa.Text),
    sa.Column("category", sa.String(1)),
)


def upgrade():
    op.execute(static_page.insert().values(
        path="/ad/sidebar/1",
        title="/store/cookbook",
        body='<img src="/static/img/rotating_ad_1.jpg">',
        category=CATEGORY_CONTENT,
    ))


def downgrade():
    op.execute(static_page.delete().where(
        static_page.c.path == "/ad/sidebar/1"))
