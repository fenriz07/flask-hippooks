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

resource_row = namedtuple("resource_row",
                          ["filename", "name", "url", "category", "manufacturer"])

parser = ArgumentParser(description='Import kitchen items')
parser.add_argument('csv', help="CSV file with kitchen item data")
parser.add_argument('photo_dir', default=".",
                    help="directory containing the photos to import")

args = parser.parse_args()


with open(args.csv, "rb ") as data:
    resources = []
    for row in csv.reader(data):
        if any(row):
            if not row[4]:
                row[4] = 'Unknown'  # add default manufacturer
            resources.append(resource_row(*(unicode(cell, "utf-8") for cell in row if cell != "")))

db.session.execute(models.ResourcesKitchen.__table__.delete())
for order, resource in enumerate(resources):
    src = join(args.photo_dir, resource.filename)
    dest = join(
        app.config["UPLOAD_FOLDER"],
        models.ResourcesKitchen.PICTURE_DIR,
        resource.filename
    )
    try:
        copy(src, dest)
    except IOError:
        error('Couldn\'t import resource "%s" from "%s" to "%s"',
              resource.name, src, dest)
    db.session.begin()
    db.session.add(models.ResourcesKitchen(
        category=resource.category,
        picture=resource.filename,
        link=resource.url,
        name=resource.name,
        manufacturer=resource.manufacturer,
        order=order,
    ))
    db.session.commit()
