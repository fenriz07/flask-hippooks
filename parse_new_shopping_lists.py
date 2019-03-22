#!/usr/bin/python
import sys
import csv
from hipcooks import models, db
import re

fptr = open(sys.argv[1], "rb")
reader = csv.reader(fptr, delimiter="\t", quotechar='"')

db.session.begin(subtransactions=True)
for cls in models.Class.query.join(models.ShoppingList)\
                .filter(models.ShoppingList.id == None):
    slist = models.ShoppingList(id=cls.id, check='')
    db.session.add(slist)
db.session.commit()

db.session.begin(subtransactions=True)
for line in reader:
    item = models.ShoppingListItem(
            category=line[2],
            shopping_list_id=int(line[0]),
            number=line[3],
            unit = line[4],
            name = line[5],
            market = line[7],
            notes = line[6],
            active = True
    )

    db.session.add(item)

db.session.commit()

fptr.close()
