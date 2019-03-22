"""Increases the length of the title and adds email templates

Revision ID: 439cca6d4887
Revises: 4dc93c32067
Create Date: 2015-11-12 00:03:37.452185

"""


# revision identifiers, used by Alembic.
revision = '439cca6d4887'
down_revision = '4dc93c32067'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    CATEGORY_EMAIL = "e"

    content = op.create_table(
        "static_page",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("path", sa.String(50), index=True, unique=True),
        sa.Column("title", sa.String(100)),
        sa.Column("body", sa.Text),
        sa.Column("category", sa.String(1)),
    )


    db.session.execute(content.insert(), [
        {"path": "/email/private-class-request",
         "title": "{{name}} sends private class inquiry from {{studio}}",
         "body": """
            Message from {{name}}<br>
            Email address: {{email}}<br>
            Phone number: {{phone}}<br>
            Date(s): {{dates}}<br>
            Menu(s): {{menus}}<br>
            For event: {{type}}<br>
            {% if contact_phone %}Contact by Phone{% endif %}<br>
            {% if contact_email %}Contact via Email{% endif %}<br>
         """,
         "category": CATEGORY_EMAIL},
        {"path": "/email/card-request",
         "title": "{{cert.sender_name}} purchased a gift card",
         "body": """
            {{cert.sender_name}} purchased a gift card<br>
            URL: <a href="http://hipcooks.com/admin/gift-certificates/edit/{{cert.id}}">
                http://hipcooks.com/admin/gift-certificates/edit/{{cert.id}}
            </a><br />
            Campus: {{cert.campus.name}}<br>
            Code: {{cert.code}}<br>
            Amount: {{cert.amount_to_give}}<br>
            Sender: {{cert.sender_name}}<br>
            Recipient: {{cert.recipient_name}}<br>
            Message: {{cert.message}}<br>
            Address:<br>
            {{cert.street_address}}<br>
            {{cert.city}}, {{cert.state}}, {{cert.zip_code}}<br>
         """,
         "category": CATEGORY_EMAIL},
        {"path": "/email/gift-certificate",
         "title": "Hipcooks gift certificate",
         "body": """
            <p>Congratulations, you lucky thing!</p>
            <p>You are well on your way to becoming a fabulous chef!</p>
            <p>This certificate is good for one cooking class of your chiece at
            {{cert.campus.name}}. You will enjoy an evening of fun and flavor,
            chopping and prepping, and, of course, wining and dining!</p>
            <p>See hipcooks.com for class description, schedule, and location
            information. To sign up, simply pay with Gift Certificate
            {{cert.code}} and you're off and cooking!</p>
            <p>Brought to you by Hipcooks and the awesome
            {{cert.sender_name}}.</p>
            <p>{{cert.message}}</p>
         """,
         "category": CATEGORY_EMAIL},
        {"path": "/email/contact",
         "title": "{{email}} sends note from {{studio}} website",
         "body": """
            Message from: {{name}}<br>
            Email address: {{email}}<br>
            At studio: {{studio}}<br>
            Note:<br>
            {{note}}<br>
         """,
         "category": CATEGORY_EMAIL},
    ])


def downgrade():
    op.drop_table("static_page")
