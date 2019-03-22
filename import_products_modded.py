#!/usr/bin/python
import sys
import os
import csv
from shutil import copy
from PIL import Image
from argparse import ArgumentParser
from hipcooks import models, db
import re

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")

parser = ArgumentParser(description='Import ingredients')
parser.add_argument('csv', help="CSV file with ingredient data")
parser.add_argument('photo_dir', default=".",
                    help="directory containing the photos to import")

args = parser.parse_args()

fptr = open(args.csv, "rb")
reader = csv.reader(fptr)

for line in reader:
    prod = models.Product.query.filter(models.Product.id == line[0]).first()
    if prod is None:
        sys.stderr.write("Can't locate product {}\n".format(line[0]))
        continue

    base_name = prod.base_name
    if line[6] != "":
        thumbnail_photo = os.path.join(args.photo_dir, line[6].replace("_", "-"))
        try:
            copy(thumbnail_photo, os.path.join(UPLOAD_FOLDER, "thumbnails", base_name))
        except Exception:
            print "{}: Couldn't find thumbnail: {}".format(prod.id, thumbnail_photo)

fptr.close()
