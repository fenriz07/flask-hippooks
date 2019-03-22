#!/usr/bin/env python

from hipcooks import db, models
from sqlalchemy.sql import expression
import lxml.html
from lxml.etree import ParserError
import re

class Unparseable(Exception):
    pass

def match_arr(name, meta):
    match = re.search(r'([\.\d\/]+)[\s\xe2]*([^\(]*)\s*(\(.*)?\s*', meta)
#    print u"Evaluating {} {}".format(unicode(name), unicode(meta))
    if match:
        qty = match.group(1)
        unit = match.group(2)
        comment = match.group(3)
        if comment is None:
            comment = ""
        return (name, qty, unit, comment)

    raise Unparseable("Can't parse arr")

def parse_purchase(food_str, category):
    items = []
    for s in food_str.split("<br />"):
        if s:
            try:
                s = s.replace("\n", "").replace("\r", "").encode("utf-8")
                tree = lxml.html.fromstring(s)
                txt = tree.text_content()
                arr = txt.split(" - ")
                if len(arr) == 2:
                    try:
                        name, qty, unit, comment = match_arr(arr[0], arr[1])
                        print "{}\t{}\t{}\t{}".format(qty, unit.encode("utf-8"), name.encode("utf-8"), comment.encode("utf-8"))
                    except Unparseable:
                        try:
                            name, qty, unit, comment = match_arr(arr[1], arr[0])
                            print "{}\t{}\t{}\t{}".format(qty, unit, name, comment)
                        except Unparseable:
                            name = s
                            qty = 1
                            unit = ""
                            comment = ""
                else:
                    name = arr[0].encode("utf-8")
                    qty = 1
                    unit = ""
                    comment = ""
                    print "{}\t\t{}\t{}".format(qty, name, comment)

                items.append(models.ShoppingListItem(number=qty, name=name, unit=unit, notes=comment, active=True, category=category, market=""))
            except ParserError:
                pass

    return items


lists = db.session.query("description_id", "`check`", "drink", "produce", "dairy", "fish_meat_poultry", "dry_goods", "frozen")\
            .select_from(expression.table("Class_shoppinglist"))\
            .all()

TYPES = [
    "drink",
    "produce",
    "dairy",
    "meat",
    "drygoods",
    "frozen",
]

for cols in lists:
    class_id = cols[0]
    db.session.begin(subtransactions=True)
    cls = db.session.query(models.Class).get(int(class_id))

    print u"Class {} ({})".format(cls.id, cls.title).encode("utf-8")
    items = []
    slist = db.session.query(models.ShoppingList).get(cls.id)
    if slist is None:
        slist = models.ShoppingList(id=cls.id)

    for i, col in enumerate(cols[2:]):
        items = items + parse_purchase(col, TYPES[i])

    slist.check = cols[1]
    slist.items = items
    db.session.add(slist)
    db.session.commit()
