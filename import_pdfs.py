#! /usr/bin/env python

from argparse import ArgumentParser
import errno
from hipcooks import app, models
from logging import info
from os import mkdir
from os.path import basename, join
from shutil import copy

parser = ArgumentParser(description='Import pdfs')
parser.add_argument('pdfs', nargs="*", help="pdfs to import")

args = parser.parse_args()

try:
    pdf_dir = join(app.config["UPLOAD_FOLDER"],
                   models.ResourcesKitchen.PDF_DIR)
    mkdir(pdf_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
    info("Directory already exists: %s", pdf_dir)

for pdf in args.pdfs:
    name = basename(pdf)
    copy(pdf, join(app.config["UPLOAD_FOLDER"],
                   models.ResourcesKitchen.PDF_DIR, name))
