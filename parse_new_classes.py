#!/usr/bin/python
import sys
import csv
from hipcooks import models, db
import re

fptr = open(sys.argv[1], "rb")
reader = csv.reader(fptr, delimiter="\t", quotechar='"')

KNIFE = dict([(re.sub(r"[^\w]", "", v.lower()), k) for k, v in models.Class.KNIFE_LEVELS.items() ])
VEGGIE = dict([(re.sub(r"[^\w]", "", v.lower()), k) for k, v in models.Class.VEGGIE_LEVELS.items() ])
DAIRY = dict([(re.sub(r"[^\w]", "", v.lower()), k) for k, v in models.Class.DAIRY_LEVELS.items() ])
WHEAT = dict([(re.sub(r"[^\w]", "", v.lower()), k) for k, v in models.Class.WHEAT_LEVELS.items() ])

db.session.begin(subtransactions=True)
for line in reader:
    cls = models.Class.query.filter(models.Class.abbr == line[0]).first()
    if cls is None:
        print "Can't find {} -- adding".format(line[0])
        cls = models.Class(
                abbr=line[0],
                description='',
                menu=''
        )
    else:
        print "Class {} is ID {}".format(line[0], cls.id)

    cls.title=line[1]
    cls.order=line[2]
    cls.knife_level=KNIFE[re.sub(r"[^\w]", "", line[3].lower())]
    cls.veggie_level=VEGGIE[re.sub(r"[^\w]", "", line[4].lower())]
    cls.dairy_level=DAIRY[re.sub(r"[^\w]", "", line[5].lower())]
    cls.wheat_level=WHEAT[re.sub(r"[^\w]", "", line[6].lower())]
    db.session.add(cls)
db.session.commit()

fptr.close()
