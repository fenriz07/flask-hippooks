from authorize import AuthorizeClient, CreditCard
from authorize.client import AuthorizeTransaction
from hipcooks import db, settings, models
from datetime import datetime
import json


class PaymentFinalizer(object):
    def __init__(self, user_id, campus, cart):
        self.user_id = user_id
        self.campus = campus
        self.cart = cart
        self.class_transaction = None
        self.product_transaction = None
        self.purchased_gift_certificates = []
        self.purchased_classes = []

    def purchase(self, number, exp_year, exp_month, cvv, first_name, last_name):

        if self.cart.total_class_cost > 0 or self.cart.product_subtotal > 0:
            if settings.CREDIT_CARD_DEBUG:
                if self.cart.total_class_cost > 0:
                    self.class_transaction = AuthorizeTransaction(None, "123456789")
                    self.class_transaction.uid = "123456789"
                if self.cart.product_subtotal > 0:
                    self.product_transaction = AuthorizeTransaction(None, "987654321")
                    self.product_transaction.uid = "987654321"
            else:
                client = AuthorizeClient(self.campus.authorize_net_login, self.campus.authorize_net_tran_key, debug=settings.CREDIT_CARD_DEBUG)
                cc = CreditCard(number, exp_year, exp_month, cvv, first_name, last_name)

                if self.cart.total_class_cost > 0:
                    self.class_transaction = client.card(cc).capture(self.cart.total_class_cost)
                if cart.product_subtotal > 0:
                    self.product_transaction = client.card(cc).capture(self.cart.product_subtotal)

            self.card_number = "{}{}".format(number[:4], "*" * (len(number) - 4))
            self.card_exp_month = exp_month
            self.card_exp_year = exp_year

    def record_purchase(self, ip_address, first_name, last_name, address1, address2, city, state, zip_code, email, phone):
        user = db.session.query(models.User).filter(models.User.id == self.user_id).first()
        db.session.begin(subtransactions=True)
        # Start by adding the overall purchase object referencing this purchase.
        purchase = models.Purchase(
            timestamp=datetime.now(),
            ip_address=ip_address,
            user_id=self.user_id,
            amount=self.cart.classes_subtotal + self.cart.product_subtotal,
            first_name=first_name,
            last_name=last_name,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            zip_code=zip_code,
            email=email,
            phone=phone,
            authorization_code="NONE",
        )
        db.session.add(purchase)

        # Then we generate gift certificates the person purchased.
        for order in self.cart.gift_certificates:
            gc = models.GiftCertificate.new_for_purchase(order)
            gc.purchase=purchase
            gc.paid_with = "CC"
            db.session.add(gc)
            self.purchased_gift_certificates.append(gc)

        # Then we generate the class orders, keeping track to match gift certs later.
        # Some of this info is duplicated, because schedule orders don't have to be
        # attached to a user (for example, if the user calls in)
        for order in self.cart.classes:
            schedule = db.session.query(models.Schedule).get(order["id"])
            cls = models.ScheduleOrder(
                    schedule_id=schedule.id,
                    user_id=self.user_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    purchase=purchase,
                    comments=order["comments"],
                    unit_price=order["price"],
                    paid=schedule.cost * (order["guests"] + 1),
                    paid_with="CC",
            )

            guests = []
            guest_info = json.loads(order['guest_info'])
            for i in range(order["guests"]):
                guest_info_dict = guest_info[i]
                new_guest = models.GuestOrder(name=guest_info_dict['name'],
                                              email=guest_info_dict['email'])
                guests.append(new_guest)
            cls.guests = guests
            db.session.add(cls)

            if len(self.cart.applied_gift_certs) > 0:
                remaining_price = cls.total_cost
                cls.paid = remaining_price
                for cert in models.GiftCertificate.query\
                                .filter(models.GiftCertificate.id.in_(self.cart.applied_gift_certs)):
                    paid = min(remaining_price, cert.amount_remaining)
                    if paid > 0:
                        record = models.Transaction(
                            purchase_id=purchase.id,
                            payment_method = "giftcert",
                            amount=paid,
                            remote_transaction_id=cert.id
                        )
                        cls.paid_with="CC + GC"
                        db.session.add(record)
                        db.session.add(models.GiftCertificateUse(
                            certificate=cert,
                            purchase=purchase,
                            amount=paid,
                        ))
                        db.session.add(cert)
                        remaining_price -= paid
                        if remaining_price == 0:
                            cls.paid_with = "GC"
            self.purchased_classes.append(cls)

        # Finally, we generate the product orders and subtract from inventory.
        if len(self.cart.products) > 0:
            cls = models.ProductOrder(
                campus_id=self.campus.id,
                online_sale=True,
                in_store_pickup=self.cart.pickup_state,
                paid_with="OnlineCC",
                date_ordered=datetime.now(),
                street_address=address1,
                city=city,
                state=state,
                zip_code=zip_code
            )
            db.session.add(cls)
            cls.assign_products(self.campus, self.cart.products,
                                self.cart.pickup_state)

        if self.class_transaction:
            class_trans_record = models.Transaction(
                purchase=purchase,
                purchase_type = 'schedule',
                payment_method = "cc",
                amount=self.cart.total_class_cost,
                card_number=self.card_number,
                exp_month=self.card_exp_month,
                exp_year=self.card_exp_year,
                remote_transaction_id=self.class_transaction.uid
            )
            db.session.add(class_trans_record)
        if self.product_transaction:
            product_trans_record = models.Transaction(
                purchase_id=purchase.id,
                purchase_type = 'product',
                payment_method = "cc",
                amount=self.cart.product_subtotal,
                card_number=self.card_number,
                exp_month=self.card_exp_month,
                exp_year=self.card_exp_year,
                remote_transaction_id=self.product_transaction.uid
            )
            db.session.add(product_trans_record)

        db.session.commit()

        return purchase


def refund(order, slots_cancelled, cc_amount_paid=None):
    transactions = db.session.query(models.Transaction)\
                        .filter(
                            models.Transaction.purchase == order.purchase,
                            models.Transaction.purchase_type == "schedule",
                            models.Transaction.payment_method == "cc",
                        )
    if cc_amount_paid:
        amount_to_refund = cc_amount_paid - float(slots_cancelled * 5)
    else:
        amount_to_refund = slots_cancelled * float(order.unit_price - 5)

    if not settings.CREDIT_CARD_DEBUG:
        client = AuthorizeClient(self.campus.authorize_net_login, self.campus.authorize_net_tran_key, debug=settings.CREDIT_CARD_DEBUG)

    for transaction in transactions:
        if settings.CREDIT_CARD_DEBUG:
            auth = AuthorizeTransaction(None, transaction.remote_transaction_id)
        else:
            auth = AuthorizeTransaction(client, transaction.remote_transaction_id)
        amt = min(amount_to_refund - settings.CANCELLATION_FEE, transaction.amount)

        if settings.CREDIT_CARD_DEBUG:
            trans = AuthorizeTransaction(None, "987654321")
            trans.uid = "987654321"
        else:
            trans = auth.credit(transaction.card_number[0:4], amt)

        amount_to_refund -= amt
        trans_record = models.Transaction(
            purchase=order.purchase,
            purchase_type='refund',
            payment_method="cc",
            amount=-amt,
            card_number=transaction.card_number,
            remote_transaction_id=trans.uid
        )
        db.session.add(trans_record)
        if amount_to_refund == 0:
            return
