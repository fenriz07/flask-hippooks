"""Makes the class information use numbers + adds drinks

Revision ID: 1c4cde6a40ec
Revises: 4e3679488f81
Create Date: 2015-07-20 16:51:28.027466

"""

# revision identifiers, used by Alembic.
revision = '1c4cde6a40ec'
down_revision = '4e3679488f81'

import csv
from itertools import count
from alembic import op
import sqlalchemy as sa
from hipcooks import db, models


knife_levels = dict(zip((
    "n/a",
    "learn great knife skills!",
    "basic knife skills taught",
    "no knifing",
), count()))

veggie_levels = dict(zip((
    "n/a",
    "vegetarian",
    "vegetarians welcome with advance notice",
    "pescatarian, vegetarians welcome with advance notice",
    "pescatarian",
    "meat-eater's class! vegetarians welcome with advance notice",
    "meat-eater's class, pescatarians welcome with advance notice",
    "meat-eater's class!",
), count()))

dairy_levels = dict(zip((
    "n/a",
    "dairy-free",
    "dairy-free welcome with advance notice",
    "not dairy-free",
), count()))

wheat_levels = dict(zip((
    "n/a",
    "wheat-free",
    "wheat-free welcome with advance notice",
    "not wheat-free",
), count()))


def upgrade():
    for column in ("knife", "veggie", "dairy", "wheat"):
        op.drop_column("Class_description", column)
    op.alter_column("Class_description", "wine",
                    new_column_name="drinks",
                    existing_type=sa.String(255),
                    existing_nullable=False)
    with open("migrations/class_data.csv") as class_data_file:
        for row in csv.reader(class_data_file):
            abbr, title, order, knife, veggie, dairy, wheat, drinks = row
            db.session.execute(
                """UPDATE Class_description
                SET
                    Class_description.order = :order,
                    Class_description.title = :title,
                    Class_description.order = :order,
                    Class_description.knife_level = :knife,
                    Class_description.veggie_level = :veggie,
                    Class_description.dairy_level = :dairy,
                    Class_description.wheat_level = :wheat,
                    Class_description.drinks = :drinks
                where abbr=:abbr""", {
                    "abbr": abbr,
                    "title": title,
                    "order": order,
                    "drinks": drinks,
                    "knife": str(knife_levels[knife]),
                    "veggie": str(veggie_levels[veggie]),
                    "dairy": str(dairy_levels[dairy]),
                    "wheat": str(wheat_levels[wheat]),
                }
            )


def downgrade():
    pass
