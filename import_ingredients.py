#! /usr/bin/env python

from argparse import ArgumentParser
from collections import namedtuple
import csv
from hipcooks import app, db, models
from logging import error
from os.path import basename, join
from shutil import copy
from sqlalchemy import func
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

resource_row = namedtuple("resource_row", ["name", "description", "filename"])

parser = ArgumentParser(description='Import ingredients')
parser.add_argument('csv', help="CSV file with ingredient data")
parser.add_argument('photo_dir', default=".",
                    help="directory containing the photos to import")

args = parser.parse_args()

with open(args.csv, "rb") as data:
    resources = [resource_row(*(unicode(cell, "utf-8")
                                for cell in row if cell != ""))
                 for row in csv.reader(data) if any(row)]
db.session.execute(models.ResourcesIngredients.__table__.delete())
for order, resource in enumerate(resources):
    src = join(args.photo_dir, resource.filename)
    dest = join(
        app.config["UPLOAD_FOLDER"],
        models.ResourcesIngredients.PICTURE_DIR,
        resource.filename
    )
    try:
        copy(src, dest)
    except IOError:
        error('Couldn\'t import resource "%s" from "%s" to "%s"',
              resource.name, src, dest)
        raise
        continue
    db.session.begin()
    db.session.add(models.ResourcesIngredients(
        picture=resource.filename,
        name=resource.name,
        description=resource.description,
        order=order,
    ))
    db.session.commit()
