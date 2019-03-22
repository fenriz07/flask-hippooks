"""Add refund email

Revision ID: 28fca49f6e9b
Revises: 20a2c4bb4f69
Create Date: 2016-03-15 15:28:54.895436

"""

# revision identifiers, used by Alembic.
revision = '28fca49f6e9b'
down_revision = '20a2c4bb4f69'

from alembic import op
import sqlalchemy as sa


CATEGORY_EMAIL = "e"

content = sa.table(
    "static_page",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("path", sa.String(50), index=True, unique=True),
    sa.Column("title", sa.String(100)),
    sa.Column("body", sa.Text),
    sa.Column("category", sa.String(1)),
)


def upgrade():

    op.bulk_insert(
        content,
        [{
            "path": "/email/refund",
            "title": "Refund completed",
            "body": """
                <p>
                    Thank you! Your reservation has been removed from the class
                    roster. Sorry it didn't work out this time. Hope to see you
                    soon!
                </p>
                <p>
                    We'll issue your refund as soon as possible - please allow
                    several business days for processing.
                </p>
                <p>
                    You will recieve an email when the refund is processed on
                    our side. Your credit card company may take a few days to
                    post the refund.
                </p>
            """,
            "category": CATEGORY_EMAIL,
        }]
    )


def downgrade():
    op.execute(content.delete().where(content.c.path == "/email/refund"))
