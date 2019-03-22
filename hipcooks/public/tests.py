from flask import url_for, session
from hipcooks import app, testing, db, models, fixtures, cart
from hipcooks.public import views
from datetime import date

class PublicTestCase(testing.DatabaseTestCase):
    datasets = [fixtures.ClassData, fixtures.CampusData, fixtures.ScheduleData]

    def test_login_required(self):
        sign_in_url = url_for("public.signin", _external=True)
        for url in (url_for(".dashboard"),
                    url_for(".mynotes"),
                    url_for(".cancel_class", order_id=1),
                    url_for(".reschedule_endpoint", id=1)):
            response = self.client.get(url)
            if response.status_code != 405:
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], sign_in_url)
            response = self.client.post(url)
            if response.status_code != 405:
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], sign_in_url)

    def test_no_login_required(self):
        schedule_id = fixtures.ScheduleData.TestClassSchedule.id
        sign_in_url = url_for("public.signin", _external=True)
        for url in (url_for(".class_details", schedule_id=schedule_id),
                    url_for(".class_landing"),
                    url_for(".class_list"),
                    url_for(".campus", id=1)):
            response = self.client.get(url)
            if response.status_code == 302:
                self.assertNotEqual(response.headers["Location"], sign_in_url)
            response = self.client.post(url)
            if response.status_code == 302:
                self.assertNotEqual(response.headers["Location"], sign_in_url)

    def test_main_page(self):
        response = self.client.get(url_for(".index"))
        self.assert200(response)

    def test_campus_select(self):
        campus_id = fixtures.CampusData.TestCampus.id
        with app.test_client() as c:
            response = c.get(url_for(".campus", id=campus_id))
            self.assertRedirects(response, url_for(".class_landing"))
            self.assertEqual(session["studio_id"], str(campus_id))

    def test_user_login(self):
        response = self.client.get(url_for(".signin"))
        self.assert200(response)

        with app.test_client() as c:
            register = c.post(url_for(".signin"), data={
                "first_name": "user_login",
                "last_name": "test",
                "phone_number": "1111111111",
                "email": "ult@parthenonsoftware.com",
                "raw_password": "password",
                "retype_password": "password",
                "register-submit": "Create Account",
            })
            self.assertRedirects(register, url_for(".dashboard"))
            self.assertEqual(session["first_name"], "user_login")
            self.assertIn("user_id", session)

        with app.test_client() as c:
            sign_in = c.post(url_for(".signin"), data={
                "email": "ult@parthenonsoftware.com",
                "password": "password",
                "sign-in-submit": "Sign In",
            })
            self.assertRedirects(sign_in, url_for(".dashboard"))
            self.assertEqual(session["first_name"], "user_login")
            self.assertIn("user_id", session)

            dashboard = c.get(url_for(".dashboard"))
            self.assertIn("user_login test", dashboard.get_data())
            self.assertIn("ult@parthenonsoftware.com", dashboard.get_data())

            posted_notes = c.post(url_for(".mynotes"), data={
                "notes": "Test note data\nsecond line",
            })
            self.assert200(posted_notes)
            user = db.session.query(models.User).get(session["user_id"])
            self.assertEqual(user.notes.notes, "Test note data\nsecond line")

            notes_in_dashboard = c.get(url_for(".dashboard"))
            self.assertIn("Test note data", notes_in_dashboard.get_data())

    def test_inject_campuses(self):
        test_campus_id = fixtures.CampusData.TestCampus.id
        with self.app.test_request_context(base_url="http://test/"):
            self.assertEqual(
                views.inject_campuses()["studio_id"].id, test_campus_id)
        session["studio_id"] = test_campus_id
        self.assertEqual(
            views.inject_campuses()["studio_id"].id, test_campus_id)

    def test_class_details(self):
        schedule = db.session.query(models.Schedule)\
                     .get(fixtures.ScheduleData.TestClassSchedule.id)
        details_url = url_for(".class_details", schedule_id=schedule.id)
        response = self.client.get(details_url)
        self.assert200(response)

        with app.test_client() as c:
            register_schedule = c.post(details_url, data={
                "register-submit": True,
                "first_name": "tcd",
                "last_name": "Test User",
                "phone_number": "1111111111",
                "email": "tcd@parthenonsoftware.com",
                "raw_password": "password",
                "retype_password": "password",
                "guests": "1",
                "cancellation_policy": True,
                "comments": "commented",
            })
            self.assertRedirects(register_schedule, url_for(".cart"))
            new_user = db.session.query(models.User)\
                         .filter_by(first_name="tcd")\
                         .one()
            self.assertEqual(new_user.email, "tcd@parthenonsoftware.com")
            new_order = db.session.query(models.ScheduleOrder)\
                          .filter_by(user=new_user)\
                          .one()

        with app.test_client() as c:
            sign_in_schedule = c.post(details_url, data={
                "sign-in-submit": True,
                "email": "tcd@parthenonsoftware.com",
                "password": "password",
                "guests": "2",
                "cancellation_policy": True,
                "comments": "More scheduling",
            })
            self.assertRedirects(sign_in_schedule, url_for(".cart"))
            newer_order = db.session.query(models.ScheduleOrder)\
                            .filter_by(comments="More scheduling")\
                            .one()
            self.assertNotEqual(new_order, newer_order)

        full_url = url_for(
            ".class_details",
            schedule_id=fixtures.ScheduleData.TestClassFullSchedule.id)
        get_waitlist = self.client.get(full_url)
        self.assertIn("waitlist", get_waitlist.get_data().lower())
        register_waitlist = self.client.post(full_url, data={
            "register-submit": True,
            "first_name": "tcd_waitlist",
            "last_name": "Test User",
            "phone_number": "1111111111",
            "email": "tcd.waitlist@parthenonsoftware.com",
            "raw_password": "password",
            "retype_password": "password",
            "guests": "1",
            "cancellation_policy": True,
            "comments": "commented",
        })
        self.assertRedirects(register_waitlist, url_for(".waitlist"))
        db.session.query(models.User)\
            .filter_by(first_name="tcd_waitlist")\
            .one()
        db.session.query(models.WaitingList)\
            .filter_by(name="tcd_waitlist")\
            .one()
        sign_in_waitlist = self.client.post(full_url, data={
            "sign-in-submit": True,
            "email": "tcd.waitlist@parthenonsoftware.com",
            "password": "password",
            "guests": "2",
            "cancellation_policy": True,
            "comments": "More scheduling",
        })
        self.assertRedirects(sign_in_waitlist, url_for(".waitlist"))
        db.session.query(models.WaitingList)\
            .filter_by(name="tcd_waitlist")\
            .filter_by(guests=2)\
            .one()
        db.session.query(models.WaitingList).delete()

    def test_cart_info(self):
        schedule = models.Schedule.query.get(
            fixtures.ScheduleData.TestClassSchedule.id)
        user = models.User.query.get(fixtures.UserData.OtherUser.id)
        num_guests = 1
        mock_session = {}
        order = cart.add_schedule(
            mock_session, schedule, user, num_guests, "No comment")
        self.assertEqual(order.schedule, schedule)
        self.assertTrue(models.ScheduleOrder.query.get(order.id))
        self.assertEqual(
            models.GuestOrder.query.filter_by(order=order).count(), num_guests)
        self.assertEqual(mock_session, {"cart_classes": [order.id]})
        self.assertEqual(cart.cart_size(mock_session), 1)
        self.assertEqual(
            views.inject_cart_info(mock_session), {"cart_size": 1})

class UserLoggedInTestCase(testing.DatabaseTestCase):
    datasets = [fixtures.UserData, fixtures.ScheduleOrderData,
                fixtures.GuestOrderData, fixtures.CampusData,
                fixtures.ScheduleData, fixtures.ClassData,
                fixtures.GiftCertificateData, fixtures.StaticPageData]

    def setUp(self):
        super(UserLoggedInTestCase, self).setUp()

        db.session.flush()
        with self.client.session_transaction() as sess:
            sess["studio_id"] = fixtures.CampusData.TestCampus.id
            sess["user_id"] = fixtures.UserData.LoggedInUser.id
            sess["first_name"] = fixtures.UserData.LoggedInUser.first_name

    def test_logout(self):
        response = self.client.get(url_for("public.logout"))
        self.assertNotIn("user_id", session)
        self.assertNotIn("first_name", session)
        self.assertRedirects(response, url_for("public.index"))

    def test_cancel_class(self):
        order_id = fixtures.ScheduleOrderData.Order.id
        title = fixtures.ClassData.TestClass.title
        guest_id = fixtures.GuestOrderData.Guest.id
        order_name = fixtures.ScheduleOrderData.Order.user.first_name
        cancel_url = url_for(".cancel_class", order_id=order_id)
        response = self.client.get(cancel_url)
        self.assert200(response)
        self.assertIn(title, response.get_data())
        self.assertIn("name=\"reschedule-submit\"", response.get_data())
        self.assertIn("name=\"refund-submit\"", response.get_data())
        self.assertNotIn("<td></td>", response.get_data())
        self.assertIn(order_name, response.get_data())
        self.assertIn("Guest", response.get_data())

        response = self.client.post(cancel_url, data={
            "reschedule-submit": True,
            "guest_cancel": guest_id,
            "order_cancel": order_id,
        })
        cert = db.session.query(models.GiftCertificate)\
                         .filter_by(message="Rescheduled")\
                         .one()
        self.assertRedirects(response,
                             url_for(".reschedule_endpoint", id=cert.id))
        self.assertTrue(
            db.session.query(models.GuestOrder).get(guest_id).cancelled)
        self.assertTrue(
            db.session.query(models.ScheduleOrder).get(order_id).cancelled)

        response = self.client.get(cancel_url)
        self.assertNotIn(order_name, response.get_data())
        self.assertNotIn("Guest", response.get_data())

        response = self.client.post(cancel_url, data={
            "refund-submit": True,
        })
        self.assertRedirects(response, url_for(".refund_endpoint"))

    def test_class_landing(self):
        landing = self.client.get(url_for(".class_landing"))
        self.assertIn("Welcome to Hipcooks", landing.get_data())

        live_class_list = self.client.get(url_for(".class_list"))
        self.assert200(live_class_list)

        url = url_for(".test_class_list")
        class_list = self.client.get(url)
        self.assert200(class_list)
        self.assertIn(fixtures.ScheduleData.TestClassSchedule.cls.title,
                      class_list.get_data())
        self.assertNotIn(fixtures.ScheduleData.TestClassOldSchedule.cls.title,
                         class_list.get_data())

    def test_cart(self):
        schedule_order = fixtures.ScheduleOrderData.UnpaidOrder
        with self.client.session_transaction() as sess:
            sess["cart_classes"] = [schedule_order.id]
        cart_url = url_for(".cart")
        cart = self.client.get(cart_url)
        self.assert200(cart)
        self.assertIn(str(2*schedule_order.unit_price), cart.get_data())

        remove_old_schedule_url = url_for(".cart_remove",
                                          schedule_order_id=schedule_order.id)
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["cart_classes"] = [schedule_order.id]
            removed = c.post(remove_old_schedule_url)
            self.assert200(removed)
            self.assertIn(str(2*schedule_order.unit_price), removed.get_data())
            self.assertNotIn(str(schedule_order.id),
                             session["cart_classes"])

        with app.test_client() as c:
            gift_cert = fixtures.GiftCertificateData.Gift
            applied = c.post(url_for(".apply_gift_certificate"), data={
                "gift_code": gift_cert.code
            })
            self.assert200(applied)
            self.assertIn(str(gift_cert.amount_to_give), applied.get_data())
            self.assertIn(gift_cert.code, session["gift_codes"])

    def test_purchase(self):
        order = models.ScheduleOrder.query.get(
            fixtures.ScheduleOrderData.UnpaidOrder.id)
        cert = models.GiftCertificate.query.get(
                fixtures.GiftCertificateData.Gift.id)
        other_cert = models.GiftCertificate.query.get(
                fixtures.GiftCertificateData.SecondGift.id)
        purchase = cart.purchase(
            models.User.query.get(fixtures.UserData.LoggedInUser.id),
            '127.0.0.1',
            schedule_orders={order: 1},
            gift_certs=[cert, other_cert]
        )
        self.assertEqual(purchase.amount, order.total_cost)
        self.assertEqual(cert.amount_to_give, 0)
        transactions = purchase.transactions
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].amount,
                         fixtures.GiftCertificateData.Gift.amount_to_give)
        self.assertEqual(transactions[0].payment_method, "giftcert")
        self.assertIsNot(order.purchase, None)

    def test_checkout(self):
        with self.client.session_transaction() as sess:
            sess["cart_classes"] = [
                str(fixtures.ScheduleOrderData.UnpaidOrder.id)
            ]
            sess["gift_codes"] = [
                fixtures.GiftCertificateData.Gift.code,
                fixtures.GiftCertificateData.SecondGift.code,
            ]
        checkout = self.client.get(
            url_for('.checkout'),
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"}
        )
        self.assert200(checkout)

    def test_static_pages(self):
        test_page_url = url_for(".pages",
                                path=fixtures.StaticPageData.Page.path)
        response = self.client.get(test_page_url)
        self.assert200(response)
        self.assertIn(fixtures.StaticPageData.Page.body, response.get_data())
