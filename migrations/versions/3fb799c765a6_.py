"""Add "We're Hiring" body to the static page editor

Revision ID: 3fb799c765a6
Revises: 28f90aab9db6
Create Date: 2016-04-04 12:06:50.420179

"""

# revision identifiers, used by Alembic.
revision = '3fb799c765a6'
down_revision = '28f90aab9db6'

from alembic import op
import sqlalchemy as sa


CATEGORY_CONTENT = "c"

content = sa.table(
    "static_page",
    sa.Column("path", sa.String(50), index=True, unique=True),
    sa.Column("title", sa.String(100)),
    sa.Column("body", sa.Text),
    sa.Column("category", sa.String(1)),
)


def upgrade():
    op.bulk_insert(content, [{
        "path": "/terms/hiring/body",
        "title": "Hipcooks: We're Hiring",
        "body": u"""
            <h3 class="JandaQuickNote-normal" style="text-align:center">We&#39;re Hiring!</h3>

            <p class="JandaQuickNote-normal"><span style="font-size:18px">Hipcooks Instructors</span></p>

            <p><img alt="" src="/static/img/hiring1.jpg" style="float:right; height:186px; width:186px" />Do you have Pizazz in the Kitchen? Are you the Host with the Most? We&#39;re often on the<br />
            lookout for teachers (full &amp; part-time) who can &quot;stand the heat!&#39;.</p>

            <p>If you&#39;ve never taken a class with us, we suggest you do. Then email &amp; tell us more.<br />
            We&#39;re specifically interested in what Hipcooks studio you&#39;re near, your cooking<br />
            experience, work experience, availability, &amp; other fun facts.</p>

            <p>&nbsp;</p>

            <p class="JandaQuickNote-normal"><span style="font-size:18px">Part-Time Day Staff</span></p>

            <p>Also, we&#39;re searching for part-time Day Staff to assist with shopping, prepping, &amp; studio maintenance.&nbsp;<br />
            You must have a love of food &amp; people, aneye for detail, &amp; work cleanly &amp; efficiently.&nbsp;<img alt="" src="/static/img/hiring2.jpg" style="float:right; height:186px; width:186px" /><br />
            No cooking experience necessary.</p>

            <p class="JandaQuickNote-normal">&nbsp;</p>

            <p class="JandaQuickNote-normal"><span style="font-size:18px">Assistant Program</span></p>

            <p>Interested in being an Assistant during our Cooking Classes?<br />
            Ask Kyrsten about our Assistant Program: We trade you Classes for Free!</p>

            <p><img alt="" src="/static/img/hiring3.jpg" style="float:left; height:186px; margin-left:25px; margin-right:25px; width:186px" /></p>

            <p>&nbsp;</p>

            <p>If you think you&#39;re a great fit, kindly send an email to<br />
            Kyrsten at <a href="mailto:Kyrsten@hipcooks.com"><span style="color:#FFA500">Kyrsten@hipcooks.com</span></a> &amp; tell us more.</p>

            <p>&nbsp;</p>

            <p>&nbsp;</p>

            <p>&nbsp;</p>

            <p>&nbsp;</p>

            <p>&nbsp;</p>

            <p>&nbsp;</p>
        """,
        "category": CATEGORY_CONTENT,
    }])


def downgrade():
    op.execute(content.delete()
               .where(content.c.path == "/terms/hiring/body"))
