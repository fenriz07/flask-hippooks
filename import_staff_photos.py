#! /usr/bin/env python

from argparse import ArgumentParser
from hipcooks import app, db, models
from logging import error
from os.path import basename, join
from shutil import copy
from sqlalchemy import func
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

parser = ArgumentParser(description='Import teacher photos')
parser.add_argument('photos', nargs="+", help="The teacher photos to import")

args = parser.parse_args()

db.session.execute(models.Teacher.__table__.update().values({"pic": None}))
for path in args.photos:
    username = basename(path).split(".", 1)[0]
    try:
        teacher = db.session.query(models.Teacher)\
            .join(models.User)\
            .filter(func.lower(models.User.username) == username.lower())\
            .one()
    except NoResultFound:
        error('Couldn\'t find user "%s" with path "%s"', username, path)
        continue
    except MultipleResultsFound:
        error('Found multiple users with name "%s" and path "%s"',
              username, path)
        continue
    new_path = join(
        app.config["UPLOAD_FOLDER"],
        models.Teacher.PICTURE_DIR,
        teacher.default_filename
    )
    copy(path, new_path)
    teacher.pic = teacher.default_filename
    db.session.begin()
    db.session.merge(teacher)
    db.session.commit()
