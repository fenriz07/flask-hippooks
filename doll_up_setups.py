#!/usr/bin/python
import sys
import os
from hipcooks import models, db

class_abbrs = [ cls.abbr for cls in models.Class.query.all() ]

db.session.begin(subtransactions=True)
for setup in models.Setup.query.all():
    setup.cleanup_text()
    db.session.add(setup)
db.session.commit()
