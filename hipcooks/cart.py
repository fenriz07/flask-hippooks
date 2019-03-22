from hipcooks import models, db, settings
from sqlalchemy import func
from datetime import datetime, timedelta
from decimal import Decimal
import uuid


class ShoppingCart(object):
    def __init__(self, session, studio=None, key=None):
        if key is None and studio is not None:
            self.key = u"shopping_cart_{}".format(studio.id)
        elif key is None:
            self.key = u"shopping_cart"
        else:
            self.key = unicode(key)
        cart = session.get(self.key, {})

        self.studio = studio
        self.classes = cart.get("classes", [])
        self._gift_certificates = cart.get("gift_certs", {})
        self.applied_gift_certs = set(cart.get("applied_gift_certs", []))
        self.product_order = cart.get("product_order", {})
        self.session = session
        self.pickup_state = cart.get("pickup", False)
        self._product_discount_percent = (
            cart.get("product_discount_percent", 0))
        self.cart_created = cart.get('cart_created', datetime.now())

    @classmethod
    def mock(cls, studio, pickup=False):
        cart = ShoppingCart({}, studio)
        cart.pickup = pickup
        return cart

    @property
    def size(self):
        return (len(self.classes) +
                len(self.gift_certificates) +
                len(self.product_order))

    def empty(self):
        self.session[self.key] = {}

    @classmethod
    def empty_all(cls, session):
        for key in session.keys():
            if key.startswith("shopping_cart"):
                del session[key]

    def _save(self):
        self.session[self.key] = self._get_dict()

    def _get_dict(self):
        return {
            "classes": self.classes,
            "gift_certs": self._gift_certificates,
            "product_order": self.product_order,
            "pickup": self.pickup_state,
            "applied_gift_certs": list(self.applied_gift_certs),
            "product_discount_percent": self.product_discount_percent,
            "cart_created": self.cart_created
        }

    @property
    def gift_certificates(self):
        return self._gift_certificates.values()

    def add_gift_certificate(self, gift_certificate_input):
        gift_certificate = dict(gift_certificate_input.items())
        cert_uuid = str(uuid.uuid4())
        gift_certificate["uuid"] = cert_uuid
        self._gift_certificates[cert_uuid] = gift_certificate
        self._save()

    def remove_gift_certificate(self, uuid):
        self._gift_certificates.pop(str(uuid), None)
        self._save()

    def apply_gift_certificate(self, certificate):
        if certificate.amount_remaining > 0:
            self.applied_gift_certs.add(certificate.id)
        self._save()

    def add_class(self, schedule, num_guests, comments, guest_info):
        self.classes.append({"id": schedule.id,
                             "title": schedule.cls.title,
                             "price": schedule.cost,
                             "guests": num_guests,
                             "comments": comments,
                             "uuid": str(uuid.uuid4()),
                             'guest_info': guest_info,
                             'total_price': schedule.cost * (1 + num_guests),
                             })
        self._save()

    def remove_class(self, uuid):
        for cls in self.classes:
            if cls["uuid"] == uuid:
                self.classes.remove(cls)
        self._save()

    def add_product(self, product, quantity):
        product_id = unicode(product.id)
        if product_id in self.product_order:
            self.product_order[product_id] += quantity
        else:
            self.product_order[product_id] = quantity
        self._save()

    def qty_product_in_cart(self, product_id):
        return self.product_order.get(unicode(product_id), 0)

    def remove_product(self, product_id):
        self.product_order.pop(unicode(product_id), None)
        self._save()

    def update_product_quantities(self, quantitymap):
        if type(quantitymap) == dict:
            for id, quantity in quantitymap.iteritems():
                if quantity < 1:
                    self.product_order.pop(unicode(id), None)
                else:
                    self.product_order[unicode(id)] = quantity
        elif type(quantitymap) == list:
            for id, quantity in quantitymap:
                if quantity < 1:
                    self.product_order.pop(unicode(id), None)
                else:
                    self.product_order[unicode(id)] = quantity
        self._save()

    def expire_on_timeout(self):
        if self.expired:
            self.empty_all(self.session)
            return True
        return False

    @property
    def products(self):
        return [ (product, self.product_order[unicode(product.id)]) for
                product in models.Product.query\
                .filter(models.Product.id.in_(self.product_order.keys()))\
                .order_by(models.Product.name)]

    @property
    def product_discount_percent(self):
        return self._product_discount_percent

    @product_discount_percent.setter
    def product_discount_percent(self, value):
        self._product_discount_percent = value
        self._save()

    @property
    def product_count(self):
        return sum(q for _, q in self.products)

    @property
    def product_tax(self):
        return sum(p.tax_price(q, self.studio.sales_tax,
                   discount=self.product_discount_percent)
                   for p, q in self.products)

    @property
    def product_subtotal(self):
        return sum(p.base_price(q)
                   for p, q in self.products)

    @property
    def product_discount(self):
        return (self.product_subtotal *
                Decimal(self.product_discount_percent)/100)

    @property
    def product_total(self):
        return (self.product_tax +
                self.product_subtotal +
                self.product_shipping -
                self.product_discount)

    @property
    def product_shipping(self):
        return sum(p.shipping_price(q, self.pickup)
                   for p, q in self.products)

    @property
    def total_class_cost(self):
        return max(self.classes_subtotal - self.applied_gift_subtotal, 0)

    @property
    def classes_subtotal(self):
        return self.schedule_subtotal + self.gift_subtotal

    @property
    def schedule_subtotal(self):
        return sum([c["price"] * (c["guests"] + 1) for c in self.classes])

    @property
    def gift_subtotal(self):
        return sum([int(g["amount_to_give"]) for g in self.gift_certificates])

    @property
    def applied_gift_subtotal(self):
        subtotal = min(
            models.GiftCertificate.total_amount(self.applied_gift_certs),
            self.classes_subtotal,
        )
        if subtotal is None:
            return 0
        return subtotal

    @property
    def pickup(self):
        return self.pickup_state

    @pickup.setter
    def pickup(self, value):
        self.pickup_state = value
        self._save()

    @property
    def payment_needed(self):
        return bool(self.product_total) or bool(self.total_class_cost)

    @property
    def totals(self):
        totals = {
            "product_tax": format(self.product_tax, "0.2f"),
            "product_subtotal": format(self.product_total, "0.2f"),
            "pickup": int(self.pickup),
            "classes_subtotal": format(self.classes_subtotal, "0.2f"),
            "applied_gift_subtotal":
                format(self.applied_gift_subtotal, "0.2f"),
            "total_class_cost": format(self.total_class_cost, "0.2f")
        }
        return totals

    @property
    def expired(self):
        return datetime.now() > self.cart_created + timedelta(minutes=settings.SHOPPING_CART_TIMEOUT_MINUTES)
