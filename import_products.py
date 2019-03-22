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

db.session.begin(subtransactions=True)
for line in reader:
    prod = models.Product.query.filter(models.Product.id == line[0]).first()
    if prod is None:
        sys.stderr.write("Can't locate product {}\n".format(line[0]))
        continue

    prod.name=line[2]
    prod.type=line[3]
    prod.splash_type = (line[4] == "YES")
    prod.description = line[5]
    prod.row = line[7]
    prod.column = line[8]
    if prod.photo is None:
        prod.photo = models.ClassPhoto()
    db.session.add(prod)

    main_photo = os.path.join(args.photo_dir, "large", line[11])
    base_name = prod.base_name
    copy(main_photo, os.path.join(UPLOAD_FOLDER, "product_images", base_name))

    if line[6] != "":
        thumbnail_photo = os.path.join(args.photo_dir, "thumbs", line[6])
        copy(thumbnail_photo, os.path.join(UPLOAD_FOLDER, "thumbnails", base_name))
    else:
        im = Image.open(main_photo)
        im.thumbnail((130,105))
        output_file = os.path.join(UPLOAD_FOLDER, 'thumbnails', base_name)
        im.save(output_file, "JPEG")

    prod.photo.photo = base_name
    db.session.add(prod)
db.session.commit()

fptr.close()
