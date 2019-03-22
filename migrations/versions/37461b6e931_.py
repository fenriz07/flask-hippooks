"""Creates forgot password email templates

Revision ID: 37461b6e931
Revises: 545bfb197c28
Create Date: 2016-01-28 22:15:10.709876

"""

# revision identifiers, used by Alembic.
revision = '37461b6e931'
down_revision = '545bfb197c28'

from alembic import op
import sqlalchemy as sa


def upgrade():
    CATEGORY_EMAIL = "e"

    content = sa.table(
        "static_page",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("path", sa.String(50), index=True, unique=True),
        sa.Column("title", sa.String(100)),
        sa.Column("body", sa.Text),
        sa.Column("category", sa.String(1)),
    )
    op.bulk_insert(content, [
        {
            "path": "/email/forgot-password",
            "title": "Forgot your password?",
            "body": """
                You can reset your password by clicking on
                <a href="{{forgot_password_link}}">this link</a>
            """,
            "category": CATEGORY_EMAIL,
        }, {
            "path": "/email/forgot-password-invalid",
            "title": "Forgot your password?",
            "body": """
                We don't have your password on record
            """,
            "category": CATEGORY_EMAIL,
        }
    ])


def downgrade():
    op.execute("""
        DELETE FROM static_page
        WHERE path like "/email/forgot-password%"
    """)
