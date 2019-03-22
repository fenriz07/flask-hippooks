#!/usr/bin/env python

from hipcooks import db, models, app, utils
from sqlalchemy.sql import expression
import os, sys, hashlib, shutil
import re

orig = sys.argv[1]

res = re.match(r"([pP]aris-\w+)-\d", os.path.basename(orig))
if res:
    abbr = res.group(1)
else:
    abbr = os.path.basename(orig).split("-")[0].upper().replace(" ", "")
print abbr
try:
    cls = models.Class.query.filter(models.Class.abbr.like(abbr))[0]
except IndexError:
    print "Cannot find class for {} from file {}".format(abbr, os.path.basename(orig))
    sys.exit(1)

photo = models.ClassPhoto(
    album=models.ClassAlbum(name="class"),
    class_id=cls.id,
    order=models.ClassPhoto.query.filter_by(class_id=cls.id).count(),
    photo='',
    caption=''
)

db.session.begin(subtransactions=True)
db.session.add(photo)
db.session.flush()
base_name = hashlib.sha1(str(photo.id) + 'class_images').hexdigest()
dest = os.path.join(app.config["UPLOAD_FOLDER"], "class_images", base_name)
print orig
print dest
shutil.copy(orig, dest)
photo.photo = base_name
utils.create_thumbnail(dest, base_name)
db.session.commit()
