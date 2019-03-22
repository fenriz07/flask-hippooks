from flask import url_for, session
from hipcooks import app, db, settings, utils, testing, fixtures, auth
from hipcooks.admin import filtering, views
from PIL import Image
from subprocess import call
import os.path
import unittest
import json
from datetime import date, time
from dateutil.relativedelta import relativedelta as rdelta
from decimal import Decimal

class AdminLoginTestCase(testing.DatabaseTestCase):
    datasets = [fixtures.UserData, fixtures.AssistantData,
                fixtures.TeacherData]

    def test_authentication(self):
        from hipcooks.models import User
        self.assertEqual(auth.authenticate_admin(
            fixtures.UserData.AssistantUser.username,
            fixtures.UserData.AssistantUser.raw_password,
        ), User.query.get(fixtures.UserData.AssistantUser.id))

        self.assertIs(auth.authenticate_admin(
            fixtures.UserData.InactiveAssistantUser.username,
            fixtures.UserData.InactiveAssistantUser.raw_password,
        ), None)

        self.assertEqual(auth.authenticate_admin(
            fixtures.UserData.TeacherUser.username,
            fixtures.UserData.TeacherUser.raw_password,
        ), User.query.get(fixtures.UserData.TeacherUser.id))

class AdminLoggedInTestCase(testing.DatabaseTestCase):
    datasets = [fixtures.ClassData, fixtures.CampusData, fixtures.ScheduleData,
                fixtures.TeacherData, fixtures.AssistantData,
                fixtures.StaticPageData, fixtures.GiftCertificateData,
                fixtures.RecipeData]

    def setUp(self):
        from hipcooks.models import User
        super(AdminLoggedInTestCase, self).setUp()
        db.session.begin(subtransactions=True)
        user = User(
            username="test_admin", first_name="Test", last_name="Admin",
            email="test.admin@parthenonsoftware.com", password="",
            is_active=True, is_superuser=True
        )
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            auth.login(user, sess)

    def test_teacher_edit_form(self):
        from hipcooks.admin.forms import TeacherEditForm
        empty_form = TeacherEditForm()
        self.assertFalse(empty_form.validate())
        minimal_form = TeacherEditForm(username="teacher",
                                       first_name="Teacher")
        self.assertTrue(minimal_form.validate())
        everything_form = TeacherEditForm(
            bio="I'm a teacher", upload_pic=None, mobile_phone="1111111111",
            home_phone="2222222222", work_phone="3333333333",
            street="street st.", city="portland", state="OR", zip_code=12555,
            ssn="1234567890", email="teacher@parthenonsoftware.com",
            username="teacher", raw_password="password", first_name="first",
            last_name="last")
        self.assertTrue(everything_form.validate())

    def test_staff_edit_view(self):
        from hipcooks.models import User, Teacher, Campus
        db.session.begin(subtransactions=True)
        tse_insert_result = db.session.execute(
            db.insert(Campus).values(domain='tse.com', name='tse_campus'))
        campus_id = tse_insert_result.inserted_primary_key
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["campus_ids"] = [campus_id]
        list_url = url_for("admin.staff_list")
        new_url = url_for("admin.staff_edit")
        response = self.client.get(new_url)
        self.assert200(response)
        self.assertTemplateUsed('/admin/staff_teacher_edit.html')
        self.assertIn('tse_campus', response.get_data())
        self.assertNotIn('checked', response.get_data())

        test_pic = os.path.join(
            settings._basedir, 'hipcooks/admin/fixtures/blank-profile-pic.png')
        response = self.client.post(new_url, data={
            'raw_password': 'password',
            'username': 'test_staff_edit_view',
            'first_name': 'Teacher',
            'bio': 'Test Bio',
            'campus': campus_id,
            'upload_pic': (test_pic, 'upload_pic')})
        self.assertRedirects(response, list_url)
        new_user = db.session.query(User)\
            .filter(User.username == 'test_staff_edit_view')\
            .one()
        self.assertTrue(new_user.valid_password('password'))
        teacher = db.session.query(Teacher).get(new_user.id)
        self.assertIsNot(teacher, None)
        os.stat(utils.path_on_disk('profile-pics', teacher.pic))

        staff_list = self.client.get(list_url)
        self.assert200(staff_list)
        self.assertIn('test_staff_edit_view', staff_list.get_data())

        edit_url = url_for("admin.staff_edit", id=new_user.id)
        response = self.client.get(edit_url)
        self.assertIn('value="test_staff_edit_view"', response.get_data())
        self.assertIn('checked', response.get_data())

        response = self.client.post(edit_url, data={
            'username': 'test_staff_edit_view_2',
            'first_name': 'Teacher',
            'upload_pic': (None, ''),
            })
        edited_user = db.session.query(User)\
            .filter(User.username == 'test_staff_edit_view_2')\
            .one()
        self.assertTrue(edited_user.valid_password('password'))
        self.assertEqual(new_user.id, edited_user.id)
        os.stat(utils.path_on_disk('profile-pics', teacher.pic))

    def test_class_edit(self):
        from hipcooks.models import Class
        new_url = url_for("admin.class_edit", id=None)
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('/admin/class.html')
        response = self.client.post(new_url, data={
            "order": 1,
            "title": "test_class_new",
            "abbr": "new_class",
            "knife_level": 1,
            "veggie_level": 1,
            "dairy_level": 1,
            "wheat_level": 1})
        self.assertEqual(response.status_code, 302)
        new_class = db.session.query(Class)\
            .filter(Class.abbr == "new_class")\
            .one()
        self.assertEqual(new_class.title, "test_class_new")

        edit_url = url_for("admin.class_edit", id=new_class.id)
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(new_class.title, response.get_data())
        response = self.client.post(edit_url, data={
            "order": 1,
            "title": "test_class_new",
            "abbr": "newer_class",
            })
        self.assertEqual(response.status_code, 302)
        edited_class = db.session.query(Class)\
            .filter(Class.abbr == "newer_class")\
            .one()
        self.assertEqual(new_class.id, edited_class.id)

        response = self.client.get(url_for("admin.class_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("test_class_new", response.get_data())

    def test_create_thumbnail(self):
        thumbnail_filename = utils.create_thumbnail(
            os.path.join(settings._basedir,
                         "hipcooks/admin/fixtures/tiny_blank_photo.png"),
            "thumbnail.jpg")
        self.assertTrue(Image.open(utils.path_on_disk('thumbnails',
                                                      thumbnail_filename)))

    def test_class_photos(self):
        from hipcooks.models import Class, ClassPhoto
        edit = self.client.post(url_for("admin.class_edit", id=None), data={
            "order": 1,
            "title": "test_class_photos",
            "abbr": "new_class",
            "knife_level": 1,
            "veggie_level": 1,
            "dairy_level": 1,
            "wheat_level": 1})
        self.assertEqual(edit.status_code, 302)
        cls = db.session.query(Class).filter(Class.abbr == "new_class").one()
        tiny_photo = os.path.join(
            settings._basedir, "hipcooks/admin/fixtures/tiny_blank_photo.png")
        new_url = url_for("admin.class_photo", class_id=cls.id, photo_id=None)
        response = self.client.post(new_url, data={
            "caption": "Testing photos",
            "photo": (tiny_photo, "photo.png")})
        photo_info = json.loads(response.get_data())
        self.assertIn("id", photo_info)
        self.assertEqual(photo_info["caption"], "Testing photos")
        os.stat(utils.path_on_disk('class_images', photo_info["photo"]))
        os.stat(utils.path_on_disk('thumbnails', photo_info["photo"]))
        self.assertEqual(ClassPhoto.query.get(photo_info["id"]).order, 0)

        response = self.client.post(new_url, data={
            "caption": "Second testing photo",
            "photo": (tiny_photo, "photo2.png")})
        self.assert200(response)
        move_url = url_for("admin.class_move_photo",
                           class_id=cls.id, moved_from=0, moved_to=1)
        response = self.client.post(move_url)
        self.assertEqual(ClassPhoto.query.get(photo_info["id"]).order, 1)
        response = self.client.post(move_url)
        self.assertEqual(ClassPhoto.query.get(photo_info["id"]).order, 0)
        response = self.client.post()

        response = self.client.get(url_for(
            "admin.class_photo", class_id='none', photo_id=photo_info["id"]))
        self.assert404(response)

        response = self.client.get(url_for(
            "admin.class_photo", class_id=cls.id, photo_id=photo_info["id"]))
        self.assert200(response)

        response = self.client.get(url_for("admin.class_edit", id=cls.id))
        self.assert200(response)

        response = self.client.post(
            url_for("admin.class_photo_delete",
                    class_id=cls.id, photo_id=photo_info["id"]))
        self.assert200(response)
        self.assertIs(db.session.query(ClassPhoto).get(photo_info["id"]), None)

    def test_assistant_list(self):
        from hipcooks.models import Assistant, User
        assistant_list_url = url_for("admin.assistant_list")
        new_assistant_url = url_for("admin.assistant_edit", assistant_id=None)
        response = self.client.post(new_assistant_url, data={
                "username": "test_assistant_list",
                "email": "test_assistant@parthenonsoftware.com",
                "raw_password": "test_password",
                "first_name": "Test",
                "last_name": "Assistant",
                "mobile_phone": "1111111111"})
        self.assertRedirects(response, assistant_list_url)
        user, assistant = db.session.query(User, Assistant)\
                            .join(Assistant)\
                            .filter(User.username == "test_assistant_list")\
                            .one()
        self.assertIsNot(assistant.id, None)
        self.assertEqual(assistant.mobile_phone, "1111111111")
        response = self.client.get(assistant_list_url)
        self.assert200(response)
        self.assertIn("Test", response.get_data())
        assistant_edit_url = url_for("admin.assistant_edit",
                                     assistant_id=assistant.id)
        response = self.client.get(assistant_edit_url)
        self.assert200(response)
        self.assertIn(fixtures.CampusData.TestCampus.name, response.get_data())
        response = self.client.post(assistant_edit_url, data={
                "username": "new_test_assistant_list",
                "email": "test_assistant@parthenonsoftware.com",
                "first_name": "Test",
                "last_name": "Assistant",
                "mobile_phone": "1111111111"})
        self.assertRedirects(response, assistant_list_url)
        self.assertEqual(db.session.query(User).get(user.id).username,
                         "new_test_assistant_list")
        response = self.client.get(assistant_edit_url)
        self.assert200(response)
        self.assertIn("new_test_assistant_list", response.get_data())
        response = self.client.get(assistant_list_url)
        self.assert200(response)

    def test_schedule_list(self):
        from hipcooks.models import Schedule
        early_event = Schedule.query.get(
            fixtures.ScheduleData.TestClassOldSchedule.id)
        middle_event = Schedule.query.get(
            fixtures.ScheduleData.TestClassFullSchedule.id)
        late_event = Schedule.query.get(
            fixtures.ScheduleData.TestClassSchedule.id)
        with self.client.session_transaction() as sess:
            sess["campus_ids"] = [fixtures.CampusData.TestCampus.id]
        list_url = url_for("admin.schedule_list")
        response = self.client.get(list_url)
        self.assert200(response)
        self.assertIn(middle_event.cls.abbr, response.get_data())
        self.assertIn(str(middle_event.spaces), response.get_data())
        self.assertIn(middle_event.teachers[0].user.first_name,
                      response.get_data())
        self.assertIn(middle_event.assistants[0].user.first_name,
                      response.get_data())
        sorted_list_url = url_for("admin.schedule_list", column="date",
                                  order="asc")
        sorted_list = self.client.get(sorted_list_url)
        self.assertLess(
            sorted_list.get_data().index(early_event.formatted_date),
            sorted_list.get_data().index(middle_event.formatted_date),
        )
        reverse_sorted_list_url = url_for("admin.schedule_list", column="date",
                                          order="desc")
        reverse_sorted_list = self.client.get(reverse_sorted_list_url)
        self.assertGreater(
            reverse_sorted_list.get_data().index(early_event.formatted_date),
            reverse_sorted_list.get_data().index(middle_event.formatted_date),
        )
        sorted_by_abbr_url = url_for("admin.schedule_list", column="abbr",
                                     order="asc")
        sorted_by_abbr = self.client.get(sorted_by_abbr_url)
        self.assert200(sorted_by_abbr)

        date_filtered_url = url_for(
            "admin.schedule_list", page=1,
            start=utils.date_string(middle_event.date),
            end=utils.date_string(middle_event.date + rdelta(weeks=1)))
        date_filtered = self.client.get(date_filtered_url)
        self.assert200(date_filtered)
        self.assertIn(middle_event.date.strftime('%a, %b, %d'),
                      date_filtered.get_data())
        self.assertNotIn(early_event.date.strftime('%a, %b, %d'),
                         date_filtered.get_data())
        self.assertNotIn(late_event.date.strftime('%a, %b, %d'),
                         date_filtered.get_data())

        private_filtered_url = url_for( "admin.schedule_list", private=True)
        private_filtered = self.client.get(private_filtered_url)
        self.assert200(private_filtered)
        self.assertIn("PTC", private_filtered.get_data())
        self.assertNotIn("TC101", private_filtered.get_data())

    def test_schedule_edit(self):
        from hipcooks.models import Schedule
        new_schedule_url = url_for("admin.schedule_edit")
        new_schedule_get = self.client.get(new_schedule_url)
        self.assert200(new_schedule_get)

        schedule_info = create_schedule_info()
        new_schedule_post = self.client.post(new_schedule_url,
                                             data=schedule_info)
        self.assertRedirects(new_schedule_post, url_for("admin.schedule_list"))
        schedule = Schedule.query.filter_by(
            date=date(1999, 9, 9), time=time(17, 30)).one()
        self.assertEqual(len(schedule.teachers), 1)
        self.assertEqual(schedule.teachers[0].user_id,
                         fixtures.TeacherData.Teacher.user.id)
        self.assertEqual(len(schedule.assistants), 1)
        self.assertEqual(schedule.assistants[0].id,
                         fixtures.AssistantData.Assistant.id)
        self.assertAlmostEqual(schedule.duration, Decimal('9.9'))

        existing_schedule_url = url_for("admin.schedule_edit", id=schedule.id)
        existing_schedule_get = self.client.get(existing_schedule_url)
        self.assertIn(
            'selected value="{}"'.format(fixtures.CampusData.TestCampus.id),
            existing_schedule_get.get_data())
        self.assertIn(
            'selected value="{}"'.format(fixtures.TeacherData.Teacher.user.id),
            existing_schedule_get.get_data())
        self.assertIn(
            'selected value="17:30"', existing_schedule_get.get_data())

        schedule_info = create_schedule_info(
            assistants=[], is_public=None, time_info="17:30")
        existing_schedule_post = self.client.post(existing_schedule_url,
                                                  data=schedule_info)
        self.assertRedirects(existing_schedule_post,
                             url_for("admin.schedule_list"))
        self.assertEqual(schedule.assistants, [])
        self.assertFalse(schedule.is_public)
        self.assertEqual(schedule.time, time(17, 30))

        schedule_info = create_schedule_info(teachers=[])
        existing_schedule_post = self.client.post(existing_schedule_url,
                                                  data=schedule_info)
        self.assertIn("This field is required.",
                      existing_schedule_post.get_data())

        schedule_info = create_schedule_info(
            cls=fixtures.ClassData.OldClass.id)
        existing_schedule_post = self.client.post(existing_schedule_url,
                                                  data=schedule_info)
        self.assertEqual(schedule.cls.id, fixtures.ClassData.OldClass.id)

    def test_inject_campus(self):
        from hipcooks.models import Campus
        empty_session = {}
        views.inject_campus(empty_session)
        self.assertEqual(views.inject_campus(empty_session), {})
        self.assertEqual(empty_session, {})
        pre_populated_session = {
            "user_id": fixtures.UserData.TeacherUser.id,
            "campus_ids": [fixtures.CampusData.OtherCampus.id],
        }
        pps_copy = dict(pre_populated_session)
        pps_context = views.inject_campus(pre_populated_session)
        self.assertEqual(
            pps_context["active_campuses"],
            [Campus.query.get(fixtures.CampusData.OtherCampus.id)])
        self.assertIn("campus_select_form", pps_context)
        self.assertEqual(pre_populated_session, pps_copy)
        user_session = {"user_id": fixtures.UserData.TeacherUser.id}
        user_context = views.inject_campus(user_session)
        self.assertEqual(user_context["active_campuses"],
                         [Campus.query.get(fixtures.CampusData.TestCampus.id)])
        self.assertIn("campus_select_form", user_context)
        self.assertEqual(user_session, {
            "user_id": fixtures.UserData.TeacherUser.id,
            "campus_ids": [fixtures.CampusData.TestCampus.id],
        })

    def test_set_campus(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess["user_id"] = fixtures.UserData.MultiCampusTeacherUser.id
            response = c.post(url_for("admin.set_campus"), data={
                "header_campuses": fixtures.CampusData.OtherCampus.id,
            })
            self.assertRedirects(response, url_for("admin.dashboard"))
            self.assertEqual(session["campus_ids"],
                             [fixtures.CampusData.OtherCampus.id])

    def test_static_pages(self):
        from hipcooks.models import StaticPage
        list_url = url_for("admin.content_list")
        response = self.client.get(list_url)
        self.assert200(response)
        self.assertIn(fixtures.StaticPageData.Page.path, response.get_data())

        page_data = {
            "path": "tsp/page",
            "title": "tsp test page",
            "body": "test",
            "category": "e",
        }
        edit_new_url = url_for("admin.content_edit")
        response = self.client.get(edit_new_url)
        self.assert200(response)
        response = self.client.post(edit_new_url, data=page_data)
        self.assertRedirects(response, list_url)
        page = StaticPage.query.filter_by(path="tsp/page").one()
        self.assertEqual(page.title, "tsp test page")

        page_data["path"] = "/tsp/page/again"
        page_data["body"] = "another test"
        edit_id_url = url_for("admin.content_edit", id=page.id)
        response = self.client.get(edit_id_url)
        self.assert200(response)
        self.assertIn("tsp test page", response.get_data())
        response = self.client.post(edit_id_url, data=page_data)
        self.assertRedirects(response, list_url)
        self.assertEqual(page.body, "another test")
        self.assertEqual(page.path, "tsp/page/again")

    def test_studios(self):
        from hipcooks.models import Campus

        list_url = url_for("admin.studio_list")
        studios = self.client.get(list_url)
        self.assert200(studios)
        self.assertIn("Test Place", studios.get_data())
        new_url = url_for("admin.studio_edit")
        new_studio = self.client.get(new_url)
        self.assert200(new_studio)
        tiny_photo = os.path.join(
            settings._basedir, "hipcooks/admin/fixtures/tiny_blank_photo.png")
        new_studio = self.client.post(new_url, data={
            "domain": "studio-edit-domain",
            "name": "Studio Edit Domain",
            "image": (tiny_photo, "photo.png"),
            "start_time": "15:00",
            "duration": 5,
        })
        self.assertRedirects(new_studio, list_url)
        studio = Campus.query.filter_by(domain="studio-edit-domain").one()
        os.stat(utils.path_on_disk(
            Campus.photo_directory, studio.photo_filename))
        edit_url = url_for("admin.studio_edit", id=studio.id)
        edit_studio = self.client.get(edit_url)
        self.assert200(edit_studio)
        self.assertIn(
            studio.photo_route,
            edit_studio.get_data(),
        )
        edit_studio = self.client.post(edit_url, data={
            "domain": "new-studio-edit-domain",
            "name": "New Studio Edit Domain",
        })
        self.assertRedirects(edit_studio, list_url)
        self.assertEqual(studio.name, "New Studio Edit Domain")

    def test_gift_certificates(self):
        from hipcooks.models import GiftCertificate
        with self.client.session_transaction() as sess:
            sess["campus_ids"] = [fixtures.CampusData.TestCampus.id]
        cert_list_url = url_for("admin.gift_certificate_list")
        cert_list = self.client.get(cert_list_url)
        self.assert200(cert_list)
        self.assertIn(fixtures.GiftCertificateData.Gift.code,
                      cert_list.get_data())
        new_url = url_for("admin.gift_certificate_edit")
        new_cert_get = self.client.get(new_url)
        self.assert200(new_cert_get)
        new_cert_post = self.client.post(new_url, data={
            "campus": fixtures.CampusData.TestCampus.id,
            "sender_name": "tgc_sender",
            "amount_to_give": "65",
            "date_sent": "",
            "paid_with": GiftCertificate.CATEGORY_CC,
            "expiration_date": "",
        })
        self.assertRedirects(new_cert_post, cert_list_url)
        cert = GiftCertificate.query.filter_by(sender_name="tgc_sender").one()
        self.assertEqual(cert.amount_to_give, 65)
        update_url = url_for("admin.gift_certificate_edit", id=cert.id)
        update_cert_post = self.client.post(update_url, data={
            "campus": fixtures.CampusData.TestCampus.id,
            "sender_name": "tgc_sender",
            "recipient_name": "tgc_recipient",
            "amount_to_give": "65",
        })
        self.assertRedirects(update_cert_post, cert_list_url)
        self.assertEqual(cert.recipient_name, "tgc_recipient")

    def test_recipes(self):
        from hipcooks.models import RecipeSet, Recipe
        class_list_url = url_for("admin.class_list")
        recipe_list_url = url_for("admin.recipe_list")
        recipe_list = self.client.get(recipe_list_url)
        self.assert200(recipe_list)
        self.assertIn(fixtures.RecipeData.TestClassRecipe.title,
                      recipe_list.get_data())
        edit_recipe_url = url_for("admin.recipe_edit",
                                  id=fixtures.ClassData.TestClass.id)
        recipe_edit_get = self.client.get(edit_recipe_url)
        self.assert200(recipe_edit_get)
        recipe_edit_post = self.client.post(edit_recipe_url, data={
            "intro": fixtures.RecipeSetData.TestClassRecipeSet.intro,
            "0-title": "New Recipe",
            "0-serves": "New Amount",
            "0-ingredients": "New Food",
            "0-instructions": "New Actions",
        })
        self.assertRedirects(recipe_edit_post, class_list_url)
        db.session.query(Recipe, RecipeSet)
        new_recipe_url = url_for("admin.recipe_edit",
                                 id=fixtures.ClassData.OldClass.id)
        recipe_new_get = self.client.get(new_recipe_url)
        self.assert200(recipe_new_get)
        recipe_new_post = self.client.post(new_recipe_url, data={
            "intro": "Introductory",
            "0-title": "New Recipe",
            "0-serves": "New Amount",
            "0-ingredients": "New Food",
            "0-instructions": "New Actions",
        })
        self.assertRedirects(recipe_new_post, class_list_url)

def create_schedule_info(**kwargs):
    schedule_info = {
        "campus": fixtures.CampusData.TestCampus.id,
        "cls": fixtures.ClassData.TestClass.id,
        "is_public": 'true',
        "is_an_event": False,
        "date": "9/9/1999",
        "time_info": "17:30",
        "duration": 9.9,
        "spaces": 99,
        "comments": "I'm a comment",
        "teachers": [fixtures.TeacherData.Teacher.user.id],
        "assistants": [fixtures.AssistantData.Assistant.id],
    }
    for arg, value in kwargs.items():
        if value is None:
            del schedule_info[arg]
        else:
            schedule_info[arg] = value
    return schedule_info
