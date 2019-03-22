"""Adds social media urls for campuses

Revision ID: 494a749ea22e
Revises: 1a5d8a96c3d
Create Date: 2015-10-29 21:43:52.268168

"""

# revision identifiers, used by Alembic.
revision = '494a749ea22e'
down_revision = '1a5d8a96c3d'

from alembic import op
import sqlalchemy as sa
from hipcooks import db


def upgrade():
    studio = sa.sql.table(
        "Class_campus",
        sa.Column("campus_id", sa.Integer, primary_key=True),
        sa.Column("facebook_url", sa.String(100)),
        sa.Column("instagram_url", sa.String(100)),
        sa.Column("google_plus_url", sa.String(100)),
        sa.Column("yelp_url", sa.String(100)),
    )

    # East LA
    db.session.execute(
        studio.update()
            .where(studio.c.campus_id == 1)
            .values({
                "facebook_url": "https://www.facebook.com/HipcooksLA",
                "instagram_url": "https://instagram.com/hipcooksla/ ",
                "google_plus_url":
                    "https://plus.google.com/114322819450733706777/about",
                "yelp_url": "http://www.yelp.com/biz/hipcooks-los-angeles",
            })
    )

    # West LA
    db.session.execute(
        studio.update()
            .where(studio.c.campus_id == 2)
            .values({
                "facebook_url": "https://www.facebook.com/HipcooksLA",
                "instagram_url": "https://instagram.com/hipcooksla/ ",
                "google_plus_url":
                    "https://plus.google.com/107542559660630945355/about",
                "yelp_url":
                    "http://www.yelp.com/biz/hipcooks-west-los-angeles",
            })
    )

    # Portland
    db.session.execute(
        studio.update()
            .where(studio.c.campus_id == 3)
            .values({
                "facebook_url": "https://www.facebook.com/HipcooksPortland",
                "instagram_url": "https://instagram.com/hipcookspdx/",
                "google_plus_url":
                    "https://plus.google.com/105637039895975074265/about",
                "yelp_url": "http://www.yelp.com/biz/hipcooks-portland",
            })
    )

    # Seattle
    db.session.execute(
        studio.update()
            .where(studio.c.campus_id == 4)
            .values({
                "facebook_url": "https://www.facebook.com/HipcooksSeattle",
                "instagram_url": "https://instagram.com/hipcooks_sea/",
                "google_plus_url":
                    "https://plus.google.com/111084846948725100174/about",
                "yelp_url": "http://www.yelp.com/biz/hipcooks-seattle",
            })
    )

    # San Diego
    db.session.execute(
        studio.update()
            .where(studio.c.campus_id == 5)
            .values({
                "facebook_url": "https://www.facebook.com/HipcooksSandiego",
                "instagram_url": "https://instagram.com/hipcookssd/ ",
                "google_plus_url":
                    "https://plus.google.com/+HipcooksSanDiego/about",
                "yelp_url": "http://www.yelp.com/biz/hipcooks-san-diego",
            })
    )

    # Orange Coun
    db.session.execute(
        studio.update()
            .where(studio.c.campus_id == 6)
            .values({
                "facebook_url": "https://www.facebook.com/HipcooksOC",
                "instagram_url": "https://instagram.com/hipcooksorangecounty/",
                "google_plus_url":
                    "https://plus.google.com/108965880522258923000/about",
                "yelp_url": "http://www.yelp.com/biz/hipcooks-santa-ana",
            })
    )


def downgrade():
    pass
