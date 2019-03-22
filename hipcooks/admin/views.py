from flask import (Blueprint, request, session, redirect, jsonify,
    render_template, url_for, abort, make_response, flash, current_app, Response,
    Markup,render_template_string)
from flask.views import MethodView
from flask.ext.sqlalchemy import Pagination
#from werkzeug.datastructures import MultiDict, CombinedMultiDict
from werkzeug.exceptions import NotFound
from sqlalchemy import and_, func, or_, literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from hipcooks import (models, db, csrf, settings, utils, email as site_emails,
                      mail, cart)
from hipcooks.auth import (
    login, admin_required, permission_required, authenticate_admin,
    is_legal_password, active_user, active_user_id)
from hipcooks.admin import sorting, filtering
from hipcooks.admin.reports import (
    gift_certificate_report, number_of_events_report, schedule_page_report,
    classes_and_occupancy_report, private_class_report, classes_taught_report,
    sales_report, sales_of_the_day_report, newsletter_subscribers_report,
    inventory_adjustments_report)
import logging
import forms
import os
import re
import hashlib
import json
from base64 import b32encode
from datetime import datetime, time, date, timedelta
from dateutil.relativedelta import relativedelta
from operator import attrgetter
from itertools import izip_longest, islice
from collections import defaultdict
from pytz import timezone

logger = logging.getLogger("admin")
blueprint = Blueprint("admin", __name__, url_prefix="/admin")


def create_admin_list(query, page, args={}, sorters={}, filters=[], default_column=None, default_order=None, per_page=100, show_all=False):
    if show_all:

        per_page = query.count()

    query_sorter = sorters.get(args.get("column", default_column))
    if query_sorter:
        query = query_sorter(query, args.get("order", default_order))

    for query_filter in filters:
        query = query_filter(query, args)

    try:
        return query.paginate(page, per_page, True)
    except AttributeError as e:
        res = query.limit(per_page).offset((page - 1) * per_page).all()
        if res:
            return Pagination(query, page, per_page, query.count(), res)
        else:
            return Pagination(query, 1, per_page, query.count(), query.limit(per_page).all())
    except NotFound:
        return query.paginate(1)


def filtered_query_count(query, args={}, filters=[]):
    for query_filter in filters:
        query = query_filter(query, args)
    return query.distinct().count()


def product_name_filters(query, args):
    if args.get('product'):
        return query.filter(models.Product.name == args.get('product'))
    return query


def crossapply_filters(filter_functions, query, args):
    for f in filter_functions:
        query = f(query, args)
    return query


def get_current_campus():
    if "campus_ids" in session and len(session["campus_ids"]) > 0:
        return session["campus_ids"][0]
    else:
        return user_campuses[0].id


@blueprint.context_processor
def inject_campus(sess=None):
    if sess is None:
        sess = session

    user_id = active_user_id()
    if user_id is None:
        return {}

    user_campuses = db.session.query(models.Campus)\
        .join(models.TeacherCampus)\
        .join(models.Teacher)\
        .filter_by(user_id=user_id)

    user = db.session.query(models.User).get(user_id)

    if "campus_ids" in sess and len(sess["campus_ids"]) > 0:
        campuses = db.session.query(models.Campus)\
            .filter(models.Campus.id.in_(sess["campus_ids"]))\
            .all()
    else:
        campuses = user_campuses.all()

    if campuses == []:
        return {}

    sess.update({
        "campus_ids": map(lambda c: c.id, campuses),
    })
    form = forms.CampusSelectForm(header_campuses=campuses)
    form.header_campuses.query = user_campuses
    return {"active_campuses": campuses, "campus_select_form": form, "user": user}


#@blueprint.context_processor
#def inject_wiki_link(sess=None):
#    return {"wiki_url": settings.HIPCOOKS_WIKI_URL}

@blueprint.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for(".login"))

@blueprint.route("/login", endpoint="login", methods=["GET", "POST", ])
def login_view():
    error = None
    form = forms.LoginForm(request.form)
    if request.method == "POST":
        if form.validate():
            user, teacher_id, assistant_id = authenticate_admin(request.form.get("username"), request.form.get("password"))
            if user is not "XTP99OAS" and user.valid_password(request.form.get("password")):
                login(user, session)
                if user.is_superuser or teacher_id:
                   teacher_campuses = db.session.query(models.Campus)\
                       .join(models.TeacherCampus)\
                       .join(models.Teacher)\
                      .filter_by(user_id=active_user_id()).all()
                   session["campus_ids"] = map(lambda c: c.id, teacher_campuses)
                   return redirect(url_for(".dashboard"))
                elif assistant_id:
                   return redirect(url_for(".assistant_schedule_signup"))
            else:
                error = "Your login attempt failed. Please try again."
                return render_template("/admin/login.html", form=form, error=error)
    return render_template("/admin/login.html", form=form, error=error)


#@blueprint.route("/dokuwiki_login", endpoint="dokuwiki_login", methods=["POST"])
#def login_view():
#    form = forms.LoginForm(request.form)
#    if request.method == "POST":
#       if form.validate():
#           user, _, _ = authenticate_admin(request.form.get("username"),
#                                           request.form.get("password"))
#           if user:
#               return jsonify(results=[user.username, user.email, user.is_superuser])
#           else:
#               return jsonify(results=[])
#       else:
#           return jsonify(results=[])


@blueprint.route("/campus/set", methods=["POST"])
def set_campus():
    form = forms.CampusSelectForm(request.form)
    form.header_campuses.query = db.session.query(models.Campus)\
        .join(models.TeacherCampus)\
        .join(models.Teacher)\
        .filter_by(user_id=active_user_id())
    if form.validate_on_submit():
        session["campus_ids"] = map(lambda c: c.id, form.header_campuses.data)
    return redirect(request.headers.get("REFERER", url_for(".dashboard")))


@blueprint.route("/", methods=["GET", ])
@admin_required
def dashboard():
    latest_note = db.session.query(models.AdminNote).order_by(models.AdminNote.ts.desc()).limit(1).first()
    return render_template("/admin/dashboard.html", latest_note=latest_note)


@blueprint.route("/change_password", methods=["GET", "POST"])
def change_password():
    form = forms.ChangePasswordForm()
    if form.validate_on_submit():
        db.session.begin()
        user = active_user()
        user.set_password(form.raw_password.data)
        db.session.merge(user)
        db.session.commit()
        flash("You've successfully changed your password.")
        return redirect(url_for(".dashboard"))
    return render_template("/admin/change_password.html", form=form)


@blueprint.route("/assistant_schedule_signup", methods=["GET", "POST"])
def assistant_schedule_signup():
    if not active_user_id():
        return redirect(url_for(".login_view"))
    assistant = db.session.query(models.Assistant)\
                          .filter(models.Assistant.user_id == active_user_id())\
                          .first()
    if not assistant:
        abort(400)

    campus_id = request.args.get('campus_id')
    if campus_id:
        if int(campus_id) not in [x.id for x in assistant.campuses]:
            abort(400)
        selected_campus = db.session.query(models.Campus).get(int(campus_id))
    else:
        selected_campus = assistant.campuses[0]

    schedules = db.session.query(models.Schedule)\
                          .filter(models.Schedule.campus == selected_campus)\
                          .filter(models.Schedule.date >= date.today())

    email_form = forms.AssistantSignupEmailForm(request.form)

    if request.method == 'POST':
        try:
            message = site_emails.assistant_email(assistant, selected_campus, email_form)
            mail.send(message)
            flash("Your request has been sent!")
        except:
            flash("There was an error sending the request email.")

    return render_template("/admin/assistant_schedule_signup.html",
                           assistant=assistant,
                           selected_campus=selected_campus,
                           schedules=schedules,
                           email_form=email_form)


@blueprint.route("/classes", methods=["GET", ])
@blueprint.route("/classes/<int:page>")
@permission_required('class')
def class_list(page=1):
    search_query = request.args.get("q", "")

    query = models.Class.query.order_by(models.Class.title.asc())
    if search_query:
        query = query.filter(or_(
                        models.Class.title.like("%{}%".format(search_query)),
                        models.Class.abbr.like("%{}%".format(search_query)),
                        models.Class.description.like("%{}%".format(search_query)),
                        models.Class.menu.like("%{}%".format(search_query)),
                    )
                )

    classes = create_admin_list(query, page)
    return render_template("/admin/class_list.html", pagination=classes, searched_field = search_query)


@blueprint.route("/class/new", methods=["GET", "POST", ], defaults={"id": None})
@blueprint.route("/class/<id>", methods=["GET", "POST", ])
@permission_required('class')
def class_edit(id):
    if id is None:
        cls = models.Class()
    else:
        cls = db.session.query(models.Class).get(id)
    form = forms.ClassForm(request.form, obj=cls)
    photos = db.session.query(models.ClassPhoto)\
                       .filter(models.ClassPhoto.class_id == id)\
                       .order_by(models.ClassPhoto.order.asc())
    if request.form and form.validate() and active_user().can_update("class"):
        form.populate_obj(cls)
        db.session.add(cls)
        db.session.flush()
        if 'save' in request.form:
            return redirect(url_for(".class_list"))
        elif 'continue' in request.form:
            return redirect(url_for(".class_edit", id=cls.id))

    return render_template(
        "/admin/class.html", class_id=id, form=form, photos=photos,
        thumbnails=(utils.url_path('thumbnails', p) for p in photos.all()))


@blueprint.route("/albums", methods=["GET", ])
@blueprint.route("/albums/<int:page>")
@permission_required('content')
def album_list(page=1):
    search_query = request.args.get("q", "")

    query = models.PhotoAlbum.query
    if search_query:
        query = query.filter(or_(
                        models.PhotoAlbum.name.like("%{}%".format(search_query)),
                    )
                )

    albums = create_admin_list(query, page)
    return render_template("/admin/album_list.html", pagination=albums, searched_field = search_query)


@blueprint.route("/album/new", methods=["GET", "POST", ], defaults={"id": None})
@blueprint.route("/album/<id>", methods=["GET", "POST", ])
@admin_required
def album_edit(id):
    if id is None:
        album = models.PhotoAlbum(active=True)
    else:
        album = db.session.query(models.PhotoAlbum).get(id)
    form = forms.PhotoAlbumEditForm(request.form, obj=album)
    photos = db.session.query(models.ClassPhoto)\
                       .filter(models.ClassPhoto.album_id == id)\
                       .order_by(models.ClassPhoto.order.asc())
    if request.form and form.validate():
        form.populate_obj(album)
        db.session.add(album)
        db.session.flush()
        if 'save_and_continue' in request.form:
            return redirect(url_for(".album_edit", id=album.id))
        elif 'save' in request.form:
            return redirect(url_for(".album_list"))

        if 'deleteAlbum' in request.form:
            db.session.begin(subtransactions=True)
            db.session.query(models.PhotoAlbum)\
                      .filter(models.PhotoAlbum.id == album.id)\
                      .delete()
            db.session.delete(album)
            db.session.commit()
            return redirect(url_for(".album_list"))

    return render_template(
        "/admin/album_edit.html", album_id=id, form=form, photos=photos,
        thumbnails=(utils.url_path('thumbnails', p) for p in photos.all()))


@blueprint.route("/class/<class_id>/photo/new",
                 methods=["POST"], defaults={"photo_id": None})
@blueprint.route("/album/<album_id>/photo/new",
                 methods=["POST"], defaults={"photo_id": None})
@blueprint.route("/class/<class_id>/photo/<photo_id>", methods=["GET", "POST"])
@blueprint.route("/album/<album_id>/photo/<photo_id>", methods=["GET", "POST"])
@csrf.exempt
def class_photo(photo_id, class_id=None, album_id=None):
    if photo_id is None and class_id is not None:
        if not active_user().can_update("class"):
            abort(403)
        cls = models.Class.query.get_or_404(class_id)
        photo = models.ClassPhoto(
            class_id=cls.id,
            order=models.ClassPhoto.query.filter_by(class_id=cls.id).count(),
            photo='',
        )
    elif photo_id is None and album_id is not None:
        if album_id and not active_user().can_update("content"):
            abort(403)
        album = models.PhotoAlbum.query.get_or_404(album_id)
        photo = models.ClassPhoto(
            album_id=album.id,
            order=models.ClassPhoto.query.filter_by(album_id=album.id).count(),
            photo='',
        )
    else:
        photo = models.ClassPhoto.query.get_or_404(photo_id)
        if str(photo.class_id) != class_id and str(photo.album_id) != album_id:
            abort(404)
    if request.form and active_user().can_update("class"):
        photo.caption = request.form["caption"]
        upload_photo = request.files["photo"]
        db.session.begin(subtransactions=True)
        db.session.add(photo)
        db.session.flush()
        base_name = hashlib.sha1(str(photo.id) + 'class_images').hexdigest()
        photo_file = utils.file_upload(
            upload_photo, base_name, 'class_images')
        photo.photo = photo_file
        utils.create_thumbnail(utils.path_on_disk('class_images', photo_file),
            photo_file,
            size=(187, 153),
        )
        db.session.commit()
    return json.dumps({"id": photo.id,
                       "caption": photo.caption,
                       "photo": photo.photo,
                       "thumbnail": utils.url_path('thumbnails', photo.photo)})

@blueprint.route("/class/<class_id>/photo/update/<photo_id>", methods=["POST"])
@blueprint.route("/album/<album_id>/photo/update/<photo_id>", methods=["POST"])
@blueprint.route("/class/<class_id>/photo/update/",
                 endpoint="class_photo_update_root", build_only=True)
@blueprint.route("/album/<album_id>/photo/update/",
                 endpoint="album_photo_update_root", build_only=True)
@csrf.exempt
def class_photo_update(photo_id, class_id=None, album_id=None):
    photo = models.ClassPhoto.query.get_or_404(photo_id)
    if str(photo.class_id) != class_id and str(photo.album_id) != album_id:
        abort(404)

    if class_id and not active_user().can_update("class"):
        abort(403)
    if album_id and not active_user().can_update("content"):
        abort(403)

    photo.caption = request.form.get("caption")
    db.session.begin(subtransactions=True)
    db.session.add(photo)
    db.session.commit()
    return jsonify(caption=request.form.get("caption"))


@blueprint.route(
    "/class/<class_id>/photo/update/<int:moved_from>/<int:moved_to>",
    methods=["POST"])
@blueprint.route(
    "/album/<album_id>/photo/update/<int:moved_from>/<int:moved_to>",
    methods=["POST"])
@blueprint.route("/class/<class_id>/photo/update/",
                 endpoint="class_move_photo_root", build_only=True)
@blueprint.route("/album/<album_id>/photo/update/",
                 endpoint="album_move_photo_root", build_only=True)

@permission_required('class')
@csrf.exempt
def class_move_photo(moved_from, moved_to, class_id=None, album_id=None):
    if class_id and not active_user().can_update("class"):
        abort(403)
    if album_id and not active_user().can_update("content"):
        abort(403)
    photos = db.session.query(models.ClassPhoto)

    if class_id is not None:
        photos = photos.filter(models.ClassPhoto.class_id == class_id)
    elif album_id is not None:
        photos = photos.filter(models.ClassPhoto.album_id == album_id)
    else:
        abort(500)

    photos = photos.order_by(models.ClassPhoto.order.asc()).all()
    photo = photos.pop(moved_from)
    photos.insert(moved_to, photo)
    db.session.begin(subtransactions=True)
    for i, photo in enumerate(photos):
        if photo.order != i:
            photo.order = i
            db.session.add(photo)
    db.session.commit()
    return jsonify(moved_to=moved_to)


@blueprint.route("/class/<class_id>/photo/<photo_id>/delete", methods=["POST"])
@permission_required('class')
@csrf.exempt
def class_photo_delete(class_id, photo_id):
    if not active_user().can_update("class") or not active_user().can_update("content"):
        abort(403)
    photo = models.ClassPhoto.query.get_or_404(photo_id)
    if class_id != str(photo.class_id):
        abort(404)
    db.session.delete(photo)
    return photo_id


@blueprint.route("/album/<album_id>/photo/<photo_id>/delete", methods=["POST"])
@permission_required('staff')
@csrf.exempt
def album_photo_delete(photo_id, album_id):
    if album_id and not active_user().can_update("content"):
        abort(403)
    photo = models.ClassPhoto.query.get_or_404(photo_id)
    if str(photo.album_id) != album_id:
        abort(404)
    photo.query.filter_by(id=photo_id).delete()
    db.session.commit()
    return photo_id


@blueprint.route("/staff", methods=["GET"], defaults={"page": 1})
@blueprint.route("/staff/page/<int:page>", methods=["GET"])
@permission_required('staff')
def staff_list(page):
    campus_ids = session.get("campus_ids", [])

    staff_query = db.session.query(models.User, models.Teacher, func.group_concat(models.TeacherCampus.role_name.distinct()))\
        .select_from(models.User)\
        .join(models.Teacher)\
        .outerjoin(models.TeacherCampus)\
        .filter(or_(models.TeacherCampus.campus_id.in_(campus_ids),
                    models.TeacherCampus.campus_id == None))\
        .group_by(models.Teacher.user_id)

    def active_filters(query, args):
        return query.filter(models.Teacher.active == (False if args.get("active", "True") == "False" else True))

    staff = create_admin_list(
        staff_query,
        page,
        request.args,
        filters=[active_filters],
        sorters=sorting.staff_criteria,
        per_page=100
    )

    staff_count = filtered_query_count(staff_query, args=request.args, filters=[])

    return render_template("/admin/staff_list.html", pagination=staff, staff_count=staff_count)


class StaffEdit(MethodView):
    decorators = [admin_required]

    def staff(self, id):
        if id is None:
            return (
                models.Teacher(),
                models.User.find_user(email=request.form.get("email")),
            )
        else:
            teacher = models.Teacher.query.get_or_404(id)
            return teacher, teacher.user

    def new_form(self, teacher, user):
        return forms.TeacherEditForm(
            request.form,
            data=dict(vars(teacher), **vars(user))
        )

    def get(self, id):
        if not active_user().can_view("staff"):
            abort(403)

        teacher, user = self.staff(id)
        form = self.new_form(teacher, user)
        return self.edit_view(form, teacher)

    def post(self, id):
        if not active_user().can_update("staff"):
            abort(403)

        teacher, user = self.staff(id)
        form = self.new_form(teacher, user)
        if form.validate_with_user(teacher, user):
            if (form.raw_password.data != '' and
                    not is_legal_password(form.raw_password.data)):
                form.raw_password.errors.append("Password too short")
            elif form.raw_password.data == '' and user.id is None:
                form.raw_password.errors.append("New staff need a password")
            else:
                db.session.begin(subtransactions=True)
                form.populate_obj(user)
                if form.raw_password.data:
                    user.set_password(form.raw_password.data)
                form.populate_obj(teacher)
                teacher.user = user
                if request.files[form.upload_pic.name]:
                    pic_file = request.files[form.upload_pic.name]
                    filename = teacher.default_filename
                    pic = utils.file_upload(
                        pic_file, filename, models.Teacher.PICTURE_DIR)
                    teacher.pic = pic
                teacher.campuses = []
                for campus_id in request.form.getlist('campus'):
                    teacher.campuses.append(models.Campus.query.get(campus_id))
                db.session.merge(teacher)
                db.session.commit()
                return redirect(url_for('.staff_list'))
        return self.edit_view(form, teacher)

    def edit_view(self, form, teacher):
        return render_template(
            '/admin/staff_teacher_edit.html', form=form, id=teacher.user_id,
            campuses=db.session.query(models.Campus,
                                      models.TeacherCampus.teacher_id)
                       .outerjoin(models.TeacherCampus, and_(
                            models.Campus.id ==
                            models.TeacherCampus.campus_id,
                            models.TeacherCampus.teacher_id ==
                            teacher.user_id)))

staff_view = StaffEdit.as_view('staff_edit')
blueprint.add_url_rule("/staff/new", defaults={"id": None},
                       view_func=staff_view)
blueprint.add_url_rule("/staff/<int:id>", view_func=staff_view)


@blueprint.route("/assistants", methods=["GET"], defaults={"page": 1})
@blueprint.route("/assistants/page/<int:page>", methods=["GET"])
@permission_required('staff')
def assistant_list(page):
    search_query = request.args.get("q", "")
    active_filter_form = forms.ActiveFilterForm(request.args)

    campus_ids = session.get("campus_ids", [])
    assistant_query = models.Assistant.query\
        .join(models.User)\
        .outerjoin(models.assistant_campuses)\
        .filter(or_(models.assistant_campuses.c.campus_id.in_(campus_ids),
                    models.assistant_campuses.c.campus_id == None))\
        .distinct()

    email_query = db.session.query(models.assistant_campuses.c.campus_id, models.Assistant.email)\
        .filter(
            models.assistant_campuses.c.campus_id.in_(campus_ids),
            models.Assistant.id == models.assistant_campuses.c.assistant_id,
            models.Assistant.active == True,
        ).distinct()
    studio_assistant_email_map = defaultdict(list)
    for tup in email_query:
        studio_assistant_email_map[tup[0]].append(tup[1])

    if active_filter_form.validate() and active_user().can_update("staff"):
        active_filters = []
        if (forms.ActiveFilterForm.FILTER_ACTIVE in
                active_filter_form.filter_activity.data):
            active_filters.append(models.Assistant.active == True)
        if (forms.ActiveFilterForm.FILTER_INACTIVE in
                active_filter_form.filter_activity.data):
            active_filters.append(models.Assistant.active == False)
        assistant_query = assistant_query.filter(or_(*active_filters))

    if search_query:
        assistant_query = assistant_query.filter(or_(
                        models.User.first_name.like("%{}%".format(search_query)),
                        models.User.last_name.like("%{}%".format(search_query)),
                        )
                )

    assistant_count = filtered_query_count(assistant_query, args=request.args, filters=[])

    assistants = create_admin_list(
        assistant_query,
        page,
        request.args,
        sorters=sorting.assistant_criteria,
        per_page=100,
    )
    return render_template(
        "/admin/assistant_list.html",
        pagination=assistants,
        args=request.args,
        searched_field=search_query,
        email_form=forms.CampusAssistantEmailForm(),
        studio_assistant_email_map=studio_assistant_email_map,
        active_filter_form=active_filter_form,
        assistant_count=assistant_count,
    )


@blueprint.route("/assistants/email", methods=["POST"])
@permission_required('staff')
def assistant_email():
    if not active_user().can_update("staff"):
        abort(403)

    form = forms.CampusAssistantEmailForm()
    form_emails = form.emails.data.split(',')
    message = site_emails.bulk_email(form.body.data,
                                     form.subject.data, [],
                                     email_list=form_emails,
                                     sender=form.campus.data.email)
    mail.send(message)
    return ""


class AssistantEdit(MethodView):
    decorators = [admin_required]

    def assistant(self, id):
        if id is None:
            return (
                models.Assistant(),
                models.User.find_user(email=request.form.get("email")),
            )
        else:
            assistant = models.Assistant.query.get_or_404(id)
            return assistant, assistant.user

    def new_form(self, assistant, user):
        return forms.AssistantEditForm(
            request.form,
            data=dict(vars(assistant), **vars(user))
        )

    def get(self, assistant_id):
        if not active_user().can_view("staff"):
            abort(403)
        assistant, user = self.assistant(assistant_id)
        form = self.new_form(assistant, user)
        return self.edit_view(form, assistant)

    def post(self, assistant_id):
        if not active_user().can_update("staff"):
            abort(403)
        assistant, user = self.assistant(assistant_id)
        form = self.new_form(assistant, user)
        if form.validate_with_user(assistant, user):
            if (form.raw_password.data != '' and
                    not is_legal_password(form.raw_password.data)):
                form.raw_password.errors.append("Password too short")
            elif form.raw_password.data == '' and assistant.id is None:
                form.raw_password.errors.append(
                    "New assistants need a password")
            else:
                db.session.begin(subtransactions=True)
                form.populate_obj(user)
                if form.raw_password.data:
                    user.set_password(form.raw_password.data)
                form.populate_obj(assistant)
                assistant.user = user
                assistant.campuses = [
                    models.Campus.query.get(campus_id)
                    for campus_id in request.form.getlist("campus")
                ]
                db.session.add(assistant)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for(".assistant_list"))
        return self.edit_view(form, assistant)

    def edit_view(self, form, assistant):
        return render_template(
            '/admin/assistant_edit.html', form=form,
            campuses=db.session.query(models.Campus,
                                      models.assistant_campuses.c.assistant_id)
                       .outerjoin(models.assistant_campuses, and_(
                            models.Campus.id ==
                            models.assistant_campuses.c.campus_id,
                            models.assistant_campuses.c.assistant_id ==
                            assistant.id)))

assistant_view = AssistantEdit.as_view('assistant_edit')
blueprint.add_url_rule("/assistant/new", defaults={"assistant_id": None},
                       view_func=assistant_view)
blueprint.add_url_rule("/assistant/<int:assistant_id>",
                       view_func=assistant_view)


@blueprint.route("/assistant/new", methods=["GET", "POST"],
                 defaults={"assistant_id": None})
@blueprint.route("/assistant/<int:assistant_id>", methods=["GET", "POST"])


@blueprint.route("/assistant/classes/<int:assistant_id>", methods=["GET"])
@permission_required('staff')
def assistant_classes(assistant_id):
    assistant = models.Assistant.query.get(assistant_id)

    return render_template(
        '/admin/assistant_classes.html',
        assistant=assistant)


@blueprint.route("/assistant/<assistant_id>/activate", methods=["POST"], defaults={"active": True})
@blueprint.route("/assistant/<assistant_id>/deactivate", methods=["POST"], defaults={"active": False})
@permission_required('staff')
def assistant_set_active(assistant_id, active):
    if not active_user().can_update("staff"):
        abort(403)

    assistant = models.Assistant.query.get_or_404(assistant_id)
    db.session.begin(subtransactions=True)
    assistant.active = active
    db.session.add(assistant)
    db.session.commit()
    return str(assistant.active)


@csrf.exempt
@blueprint.route("/staff/permissions/<id>", methods=["GET", "POST",], defaults={"campus_id": None})
@blueprint.route("/staff/permissions/<id>/campus/<campus_id>", methods=["GET", "POST",])
@permission_required('staff')
def staff_permissions(id, campus_id):
    teacher = db.session.query(models.Teacher).filter(models.Teacher.user_id == id).first()

    if campus_id:
        campus = db.session.query(models.Campus).get(campus_id)
    else:
        campus = teacher.campuses[0]

    perms = db.session.query(models.PermissionType, models.Permission)\
                .select_from(models.PermissionType)\
                .outerjoin(models.Permission,
                    and_(
                        models.Permission.user_id == teacher.user_id,
                        models.Permission.campus_id == campus.id,
                        models.Permission.permission_type_id == models.PermissionType.id
                    )
                )\
                .order_by(models.PermissionType.name)

    tc = models.TeacherCampus.query\
            .filter(models.TeacherCampus.teacher_id == teacher.user_id,
                    models.TeacherCampus.campus_id == campus.id)[0]

    for preset in settings.GROUP_MACROS:
        if preset['name'] == tc.role_name:
            selected_preset = tc.role_name
            break
    else:
        selected_preset = None

    if request.method == "POST" and active_user().can_update("staff"):
        permission_matrix = {}
        for permission_type_obj, permission_obj in perms:
            if permission_obj:
                permission_obj.can_view = False
                permission_obj.can_update = False
                permission_matrix[str(permission_type_obj.id)] = permission_obj
            else:
                permission_matrix[str(permission_type_obj.id)] = models.Permission(
                                                            user_id = id,
                                                            campus_id = campus.id,
                                                            permission_type_id = permission_type_obj.id
                                                        )

        for permission in request.form.getlist("permissions"):
            perm_type_id, view_or_edit = permission.split("_")
            if view_or_edit == "view":
                permission_matrix[perm_type_id].can_view = True
            if view_or_edit == "edit":
                permission_matrix[perm_type_id].can_update = True

        db.session.begin(subtransactions=True)
        if request.form.get("role_name", "") != "":
            try:
                tc = models.TeacherCampus.query\
                        .filter(models.TeacherCampus.teacher_id == teacher.user_id,
                                models.TeacherCampus.campus_id == campus.id)[0]
                tc.role_name = request.form.get("role_name")
                db.session.merge(tc)
            except IndexError:
                pass
        for permission_obj in permission_matrix.values():
            db.session.add(permission_obj)
        db.session.commit()
        return redirect(url_for(".staff_permissions", id=id, campus_id=campus_id))

    return render_template("/admin/staff_perms.html",
                           perms=perms,
                           teacher=teacher,
                           campus=campus,
                           presets=settings.GROUP_MACROS,
                           selected_preset=selected_preset)


@blueprint.route("/schedules", defaults={"page": 1})
@blueprint.route("/schedules/page/<int:page>")
@blueprint.route("/schedules/page/1", endpoint="schedule_list_base",
                 build_only=True, defaults={"page": 1})
@blueprint.route("/schedules/page/<int:page>/<start>/<end>")
@permission_required('schedule')
def schedule_list(page, start=None, end=None):
    search_query = request.args.get("q", "")
    deleted = request.args.get('deleted', '')
    schedule_type = request.args.get('schedule_type', '')

    if start is None or end is None:
        today = date.today()
        start_date = today + relativedelta(day=1)
        end_date = today + relativedelta(day=1, months=+1)
        date_filter = _filter_date_range(start_date, end_date)
    elif start == 'all' and end == 'all':
        start_date = None
        end_date = None
        def date_filter(query, args):
            return query
    else:
        start_date = utils.from_date_string(start)
        end_date = utils.from_date_string(end)
        date_filter = _filter_date_range(start_date, end_date)

    schedule_query = models.Schedule.query\
        .filter(models.Schedule.campus_id.in_(session.get("campus_ids", [])))\
        .join(models.Class)\
        .join(models.Campus)\
        .outerjoin(models.Teacher, models.Schedule.teachers)\
        .join(models.User, models.Teacher.user_id == models.User.id)

    if search_query:
        schedule_query = schedule_query.filter(or_(
                        models.Class.title.like("%{}%".format(search_query)),
                        models.User.first_name.like("%{}%".format(search_query)),
                        models.Class.abbr == search_query
                        )
                )

    filters = [_filter_schedule_type, _filter_deleted, date_filter]

    schedules = create_admin_list(
        schedule_query,
        page,
        request.args,
        sorters=sorting.schedule_criteria,
        filters=filters,
        default_column="date",
        default_order="asc",
    )

    schedule_count = filtered_query_count(schedule_query, args=request.args, filters=filters)

    date_back = [utils.date_back(start_date, end_date)]
    date_range, show_dates, range_view = utils.schedule_date_range(start_date, end_date)
    dates_combined = [date_back] + date_range
    date_lists = [dates_combined[x:x + 10] for x in xrange(0, len(dates_combined), 10)]

    show_all = range_view == 'month'

    return render_template(
        "/admin/schedule_list.html",
        pagination=schedules,
        args=request.args,
        today=date.today(),
        start=start_date or 'all',
        end=end_date or 'all',
        searched_field=search_query,
        date_range=date_range,
        date_back=date_back[0],
        date_lists=date_lists,
        show_dates=show_dates,
        deleted=deleted,
        schedule_type=schedule_type,
        label='schedule',
        schedule_count=schedule_count,
        show_all=show_all,
    )


def _filter_schedule_type(query, args):
    schedule_type = args.get('schedule_type', '')
    if schedule_type == 'private':
        return query.filter(models.Schedule.is_public == False)
    elif schedule_type == 'public':
        return query.filter(models.Schedule.is_public == True)
    elif schedule_type == 'event':
        return query.filter(models.Schedule.is_an_event == True)
    else:
        return query


def _filter_deleted(query, args):
    deleted = args.get('deleted', '')
    if deleted == 'true':
        return query.filter(models.Schedule.deleted == True)
    else:
        return query.filter(or_(models.Schedule.deleted == False, models.Schedule.deleted == None))


def _filter_date_range(start_date, end_date):
    def _filter_date_range(query, args):
        return query.filter(models.Schedule.date >= start_date)\
            .filter(models.Schedule.date < end_date)
    return _filter_date_range


@blueprint.route("/schedules/new", methods=["GET", "POST"],
                 defaults={"id": None})
@blueprint.route("/schedules/<id>", methods=["GET", "POST"])
@permission_required('schedule')
def schedule_edit(id):
    if id is None:
        schedule = models.Schedule(is_public=True)
    else:
        schedule = db.session.query(models.Schedule).get(id)
        schedule.time_info = schedule.time.strftime("%H:%M")
    preexisting_schedule_assistants = schedule.assistants
    form = forms.ScheduleEditForm(request.form, schedule)
    if form.validate_on_submit() and active_user().can_update("schedule", campus_id=request.form.get("campus_id")):
        form.populate_obj(schedule)
        schedule.time = time(*map(int, schedule.time_info.split(":")))
        db.session.begin(subtransactions=True)
        db.session.add(schedule)

        # adjust assistant class fields
        if preexisting_schedule_assistants:
            for current_assistant in schedule.assistants:
                if current_assistant not in preexisting_schedule_assistants:
                    current_assistant.classes += 1
                    db.session.add(current_assistant)
            for preexisting_assistant in preexisting_schedule_assistants:
                if preexisting_assistant not in schedule.assistants:
                    if preexisting_assistant.classes > 0:
                        preexisting_assistant.classes -= 1
                        db.session.add(preexisting_assistant)
        else:
            for current_assistant in schedule.assistants:
                current_assistant.classes += 1
                db.session.add(current_assistant)

        db.session.commit()
        if request.form.get("save_continue"):
            return redirect(url_for(".schedule_edit", id=schedule.id))
        elif request.form.get("save_add"):
            return redirect(url_for(".schedule_edit"))
        elif request.form.get("deleteSchedule"):
            db.session.begin(subtransactions=True)
            db.session.query(models.Schedule)\
                      .filter(models.Schedule.id == schedule.id)\
                      .delete()
            db.session.delete(schedule)
            db.session.commit()
            return redirect(url_for("admin.schedule_list"))
        else:
            return redirect(url_for("admin.schedule_list"))


    studios = db.session.query(models.Campus)

    return render_template("/admin/schedule_edit.html",
                            form=form,
                            schedule=schedule,
                            studios=studios,
                            studio_teacher_map=form.studio_teacher_map().iteritems(),
                            studio_assistant_map=form.studio_assistant_map().iteritems())


@blueprint.route("/schedules/reservations/<id>")
@permission_required('schedule')
def schedule_reservations(id):
    schedule = db.session.query(models.Schedule).get(id)
    orders = db.session.query(models.ScheduleOrder)\
        .join(models.Schedule)\
        .filter(models.Schedule.id == id)\
        .filter(models.ScheduleOrder.cancelled != True)
    waitlists = db.session.query(models.WaitingList)\
                          .filter(models.WaitingList.schedule_id == schedule.id)\
                          .order_by(models.WaitingList.tstamp.asc()).all()

    emails = db.session.query(models.ScheduleOrder.email)\
                .filter(
                    models.ScheduleOrder.schedule_id == id,
                    models.ScheduleOrder.cancelled == False,
                ).all()
    emails = [x[0] for x in emails]
    email_form = forms.BulkEmailForm()
    email_string = ','.join(str(x) for x in emails)
    email_form.emails.data = email_string
    email_form.from_email.data = schedule.campus.email
    return render_template("/admin/schedule_reservations.html",
                           schedule=schedule, orders=orders, waitlists=waitlists,
                           from_email=settings.MAIL_EMAIL_ADDRESS,
                           email_form=email_form)


@blueprint.route("/schedules/email/<schedule_id>", methods=["POST"])
@permission_required('schedule')
def schedule_email(schedule_id):
    emails = db.session.query(models.ScheduleOrder.email)\
                .filter(
                    models.ScheduleOrder.schedule_id == id,
                    models.ScheduleOrder.cancelled == False,
                ).all()
    schedule = models.Schedule.query.get(schedule_id)
    if not active_user().can_update("schedule", campus_id=schedule.campus.id):
        abort(403)

    form = forms.BulkEmailForm()
    form_emails = form.emails.data.split(',')
    queried_emails = [x[0] for x in emails]
    additional_emails = list(set(form_emails) - set(queried_emails))
    message = site_emails.bulk_email(form.body.data, form.subject.data, emails, email_list=additional_emails)
    mail.send(message)
    return ""


@blueprint.route("/schedules/class/list/<schedule_id>")
@permission_required('schedule')
def schedule_class_list(schedule_id):
    schedule = db.session.query(models.Schedule).get(schedule_id)
    orders = db.session.query(models.ScheduleOrder)\
        .join(models.Schedule)\
        .filter_by(id=schedule_id)
    return render_template("/admin/schedule_class_list.html",
                           schedule=schedule, orders=orders)


@blueprint.route("/schedules/report/<id>", methods=["GET", "POST"])
@permission_required('schedule_report')
def schedule_report(id):
    db.session.begin(subtransactions=True)
    report = db.session.query(models.ClassReport).get(id)
    schedule = db.session.query(models.Schedule).get(id)
    if report is None:
        report = models.ClassReport(id=id, schedule=schedule, draft=True)

    sales = db.session.query(models.ProductOrder, models.ProductOrderItem, models.Product)\
                .select_from(models.ProductOrder)\
                .join(models.ProductOrderItem)\
                .join(models.Product)\
                .filter(
                    models.ProductOrder.campus == schedule.campus,
                    models.ProductOrder.online_sale == False,
                    models.ProductOrder.date_ordered >= schedule.date,
                    models.ProductOrder.date_ordered < schedule.date + timedelta(days=1)
                )\
                .group_by(models.ProductOrder.sold_by_id)\
                .all()

    # Intercept addition of just comment
    if request.form.get("send_comment", False) \
            and len(request.form.get("comment", "")) > 0 \
            and active_user().can_update("schedule_report", campus_id=schedule.campus.id):
        new_comment = models.ClassReportComment(
                                report_id=report.id,
                                teacher_id=active_user_id(),
                                comment=request.form.get("comment")
                        )
        db.session.add(new_comment)
        db.session.commit()

        recipient_list = request.form.getlist("comments_to")
        if len(recipient_list) > 0:
            message = site_emails.class_report_comment(report, new_comment, recipient_list)
            mail.send(message)
        return redirect(url_for(".schedule_report", id=id))

    form = forms.ClassReportForm(request.form, obj=report)
    if form.validate_on_submit() \
            and active_user().can_update("schedule_report", campus_id=schedule.campus.id):
        form.populate_obj(report)
        if not request.form.get("draft", False):
            report.draft = False

        # Populate participant updates from the lists of no-shows and people
        # who expressed interest in assisting.
        participants = db.session.query(models.ScheduleOrder)\
            .filter(models.ScheduleOrder.schedule_id==report.id)
        noshows = set([int(noshow.split("_")[1]) for noshow in request.form.getlist("noshows")])
        assistants = [int(assistant) for assistant in request.form.getlist("assistants")]
        res_ids = request.form.getlist("reservation_ids")
        res_first_names = request.form.getlist("reservation_first_names")
        res_last_names = request.form.getlist("reservation_last_names")
        res_emails = request.form.getlist("reservation_emails")
        reservation_lookup = dict([(int(z[0]), z[1:]) for z in zip(res_ids, res_first_names, res_last_names, res_emails)])

        db.session.add(report)

        for participant in participants:
            if participant.user_id is not None:
                if int(participant.user_id) in noshows:
                    participant.no_show = True
                else:
                    participant.no_show = False
                if int(participant.user_id) in assistants:
                    participant.interested_in_assisting = True
                else:
                    participant.interested_in_assisting = False
                try:
                    part = reservation_lookup[int(participant.id)]
                    participant.user.first_name = part[0]
                    participant.user.last_name = part[1]
                    participant.user.email = part[2]
                except KeyError:
                    pass

                db.session.add(participant)

        # Add the extra folks
        report.schedule.extra_people = []
        extra_names = request.form.getlist("extra_student_names")
        extra_emails = request.form.getlist("extra_student_emails")
        extra_payments = request.form.getlist("extra_student_payments")
        for name, email, payment in zip(extra_names, extra_emails, extra_payments):
            report.schedule.extra_people.append(
                models.ExtraPerson(name=name, email=email, how_paid=payment)
            )

        # Add substitutes -- extras are already added...
        sub_originals = request.form.getlist("sub_original_ids")
        sub_names = request.form.getlist("sub_student_names")
        sub_emails = request.form.getlist("sub_student_emails")
        for name, email, original in zip(sub_names, sub_emails, sub_originals):
            report.schedule.extra_people.append(
                models.ExtraPerson(name=name, email=email, how_paid='NA', order_id=int(original))
            )
        db.session.commit()
        if not report.draft:
            message = site_emails.class_report(report)
            mail.send(message)
        return redirect(url_for(".schedule_report", id=id))
    else:
        db.session.rollback()

    return render_template("/admin/class_report.html", form=form, report=report, sales=sales)


@blueprint.route("/content/list")
@blueprint.route("/content/list/<int:page>")
@permission_required('content')
def content_list(page=1):
    pages = create_admin_list(models.StaticPage.query, page, per_page=100)
    return render_template("/admin/content_list.html", pagination=pages)


@blueprint.route("/classes/classes_report")
@permission_required('class')
def classes_report():
    db.session.begin()
    classes = db.session.query(models.Class.order,models.Class.title)\
    .select_from(models.Class)\
    .order_by(models.Class.order)
    return render_template("/admin/classes_report.html", classes=classes)


@blueprint.route("/content/edit/new", methods=["GET", "POST"],
                 defaults={"id": None})
@blueprint.route("/content/edit/<id>", methods=["GET", "POST"])
@permission_required('content')
def content_edit(id):
    if id is None:
        page = models.StaticPage()
    else:
        page = db.session.query(models.StaticPage).get(id)
    form = forms.StaticContentEditForm(request.form, page)
    if form.validate_on_submit() and active_user().can_update("content"):
        form.populate_obj(page)
        db.session.begin(subtransactions=True)
        db.session.add(page)
        try:
            db.session.commit()
        except IntegrityError:
            form.path.errors.append("Path already in use")
            db.session.rollback()
        else:
            return redirect(url_for(".content_list"))
    return render_template("/admin/content_edit.html", form=form)


@blueprint.route("/studios", methods=["GET"])
@blueprint.route("/studios/<int:page>")
@permission_required('campus')
def studio_list(page=1):
    studios = create_admin_list(models.Campus.query, page)
    return render_template("/admin/studio_list.html", pagination=studios)


@blueprint.route("/studio/new", methods=["GET", "POST"], defaults={"id": None})
@blueprint.route("/studio/<id>", methods=["GET", "POST"])
@permission_required('campus')
def studio_edit(id):
    if id is None:
        studio = models.Campus()
    else:
        studio = db.session.query(models.Campus).get(id)
    info = CombinedMultiDict((request.form, request.files))
    form = forms.StudioEditForm(info, obj=studio)
    if studio.start_time:
        form.start_time.data = studio.start_time.strftime('%H:%M')
    if request.form and form.validate() and active_user().can_update("campus"):
        db.session.begin(subtransactions=True)
        form.populate_obj(studio)
        start_time = datetime.strptime(request.form['start_time'], '%H:%M')
        studio.start_time = datetime.strptime(request.form['start_time'], '%H:%M')\
                                    .time()
        db.session.add(studio)

        if request.files.get(form.image.name):
            photo_file = request.files[form.image.name]
            utils.file_upload(
                photo_file,
                studio.photo_filename,
                models.Campus.photo_directory
            )
        db.session.commit()

        return redirect(url_for(".studio_list"))
    return render_template(
        "/admin/studio_edit.html", studio=studio, form=form)


@blueprint.route("/gift-certificates", defaults={"page": 1})
@blueprint.route("/gift-certificates/<int:page>")
@permission_required('giftcertificate')
def gift_certificate_list(page):
    search_query = request.args.get("q", "")
    campus_ids = session.get("campus_ids", [])

    cert_query = db.session.query(
            models.GiftCertificate,
            (models.GiftCertificate.amount_to_give -
             func.IFNULL(func.SUM(models.GiftCertificateUse.amount), 0))
            .label("amount_remaining"),
        )\
        .join(models.Campus)\
        .outerjoin(models.GiftCertificateUse,
                   models.GiftCertificate.id ==
                   models.GiftCertificateUse.certificate_id)\
        .group_by(models.GiftCertificate.id)\
        .filter(models.GiftCertificate.campus_id.in_(campus_ids))

    if search_query:
        cert_query = cert_query.filter(or_(
                        models.GiftCertificate.sender_name.like("%{}%".format(search_query)),
                        models.GiftCertificate.sender_email.like("%{}%".format(search_query)),
                        models.GiftCertificate.recipient_name.like("%{}%".format(search_query)),
                        models.GiftCertificate.code.like("%{}%".format(search_query)),
                    )
                )

    def cert_filters(query, args):
        if args.get("paid_with", None):
            return query.filter(models.GiftCertificate.paid_with == args.get("paid_with", "True"))
        else:
            return query

    gc_count = filtered_query_count(cert_query, args=request.args, filters=[cert_filters])

    certs = create_admin_list(
        cert_query,
        page,
        request.args,
        sorters=sorting.gift_certificate_criteria,
        filters=[cert_filters],
        default_column='created',
        default_order='desc',
        per_page=100
    )
    return render_template("/admin/gift_certificate_list.html",
                           pagination=certs,
                           gc_count=gc_count)


@blueprint.route("/gift-certificates/edit/new", methods=["GET", "POST"],
                 defaults={"id": None})
@blueprint.route("/gift-certificates/edit/<id>", methods=["GET", "POST"])
@permission_required('giftcertificate')
def gift_certificate_edit(id):
    if id is None:
        cert = models.GiftCertificate(code=b32encode(os.urandom(5))[:7])
        preexisting_amount_remaining = 0
        cert_exists = False
    else:
        cert = db.session.query(models.GiftCertificate).get(id)
        cert.form_amount_remaining = cert.amount_remaining
        preexisting_amount_remaining = cert.amount_remaining
        cert_exists = True

    if 'delete' in request.form:
        db.session.begin(subtransactions=True)
        db.session.query(models.GiftCertificateUse)\
                  .filter(models.GiftCertificateUse.certificate_id == cert.id)\
                  .delete()
        db.session.delete(cert)
        db.session.commit()
        return redirect(url_for(".gift_certificate_list"))

    email_form = forms.GiftCertificateEmailForm()
    if cert.id:
        email_form.from_email.data = cert.campus.email
        sender_email = cert.sender_email
        recipient_email = cert.recipient_email
        email_form.date_sent.data = cert.date_sent
    else:
        sender_email = None
        recipient_email = None

    form = forms.GiftCertificateEditForm(request.form, cert)
    if form.validate_on_submit() and active_user().can_update("giftcertificate"):
        form.populate_obj(cert)
        db.session.begin(subtransactions=True)
        if cert.id is None:
            cert.amount_to_give = cert.form_amount_remaining
        else:
            db.session.add(models.GiftCertificateUse(
                certificate=cert,
                purchase_id=None,
                amount=cert.amount_remaining - cert.form_amount_remaining,
            ))
        db.session.add(cert)
        db.session.commit()

        cert.adjust_assistant_credits(preexisting_amount_remaining,
                                      form.form_amount_remaining.data,
                                      cert_exists)
        if 'save' in request.form:
            return redirect(url_for(".gift_certificate_list"))
        elif 'save_and_continue' in request.form:
            return redirect(url_for(".gift_certificate_edit", id=cert.id))
        elif 'save_add_another' in request.form:
            return redirect(url_for(".gift_certificate_edit", id=None))

    return render_template("/admin/gift_certificate_edit.html",
                           form=form,
                           email_form=email_form,
                           cert=cert,
                           sender_email=sender_email,
                           recipient_email=recipient_email)


@blueprint.route("/gift-certificate-blocks", defaults={"page": 1})
@blueprint.route("/gift-certificate-blocks/<int:page>")
@permission_required('giftcertificate')
def gift_certificate_block_list(page):
    campus_ids = session.get("campus_ids", [])
    cert_query = models.GiftCertificateBlock.query\
        .filter(models.GiftCertificateBlock.campus_id.in_(campus_ids))
    certs = create_admin_list(cert_query, page, per_page=100)
    return render_template("/admin/gift_certificate_block_list.html",
                           pagination=certs)


@blueprint.route("/gift-certificate-blocks/edit/new", methods=["GET", "POST"],
                 defaults={"id": None})
@blueprint.route("/gift-certificate-blocks/edit/<id>", methods=["GET", "POST"])
@permission_required('giftcertificate')
def gift_certificate_block_edit(id):
    if id is None:
        block = models.GiftCertificateBlock()
    else:
        block = db.session.query(models.GiftCertificateBlock).get(id)

    if 'delete' in request.form:
        db.session.begin(subtransactions=True)
        for cert in block.gift_certificates:
            db.session.query(models.GiftCertificateUse)\
                      .filter(models.GiftCertificateUse.certificate_id == cert.id)\
                      .delete()
            db.session.delete(cert)
        db.session.delete(block)
        db.session.commit()
        return redirect(url_for(".gift_certificate_block_list"))

    form = forms.GiftCertificateBlockEditForm(request.form, block)
    if form.validate_on_submit() and active_user().can_update("giftcertificate"):
        db.session.begin(subtransactions=True)

        form.populate_obj(block)
        block.last_updated = datetime.now()
        db.session.add(block)
        db.session.commit()
        if id is None:
            db.session.begin(subtransactions=True)
            for i in range(0, block.total_certs):
                cert = block.generate_cert()
                db.session.add(cert)
                cert.adjust_assistant_credits(0,
                                              cert.amount_to_give,
                                              False)
            db.session.commit()
        else:
            db.session.begin(subtransactions=True)
            for cert in db.session.query(models.GiftCertificate)\
                    .outerjoin(models.GiftCertificateUse)\
                    .filter(models.GiftCertificate.block_id == block.id)\
                    .filter(models.GiftCertificateUse.id == None):
                preexisting_amount_to_give = cert.amount_to_give
                cert.amount_to_give = block.amount_to_give
                db.session.add(cert)
                cert.adjust_assistant_credits(preexisting_amount_to_give,
                                              cert.amount_to_give,
                                              True)
            db.session.commit()
        return redirect(url_for(".gift_certificate_block_list"))
    return render_template("/admin/gift_certificate_block_edit.html", form=form)


@blueprint.route("/recipes", defaults={"page": 1})
@blueprint.route("/recipes/<int:page>")
@permission_required('class_recipes')
def recipe_list(page):
    query = db.session.query(models.RecipeSet).join(models.Class).order_by(models.Class.abbr.asc())
    recipes = create_admin_list(
        query,
        page,
        args=request.args,
        show_all=True
    )
    return render_template("/admin/recipe_list.html", pagination=recipes)


@blueprint.route("/recipes/email/<int:id>", methods=["GET", "POST"])
def recipe_email(id):
    current_campus = get_current_campus()
    recipe = models.RecipeSet.query.get_or_404(id)
    cls = recipe.cls
    form = forms.RecipeEmailForm(cls)
    campus_obj = models.Campus.query.get(current_campus)

    if campus_obj.email:
        form.from_.data = campus_obj.email
    else:
        form.from_.data = "noreply@hipcooks.com"
    if form.validate_on_submit():
        env = utils.nonHTMLJinjaEnv()
        header_image = utils.base_64_encoded_file('static/img/printheadergraphic.png')
        template = env.get_template("/recipe_preview.html").render(recipe_set=recipe,
                                                                   cls=cls,
                                                                   header_image=header_image)
        messages = site_emails.bulk_email_recipe(form, template)
        for message in messages:
            try:
                mail.send(message)
                flash("Email sent to {}".format(message.recipients[0]))
            except Exception as e:
                logging.exception(e)
                flash(Markup("""
                    <span class="text-danger">
                        Email not sent to {}
                    </span>
                    """).format(message.recipients[0]))
    return render_template("/admin/recipe_email.html", form=form)


@blueprint.route("/setups", defaults={"page": 1})
@blueprint.route("/setups/<int:page>")
@permission_required('class_setups')
def setup_list(page):
    query = db.session.query(models.Setup).join(models.Class).order_by(models.Class.abbr.asc())
    setups = create_admin_list(
        query,
        page,
        args=request.args,
        show_all=True
    )
    return render_template("/admin/setup_list.html", pagination=setups)


@blueprint.route("/recipes/edit/new", defaults={"class_id": None}, methods=["GET", "POST"])
@blueprint.route("/recipes/edit/<int:class_id>", methods=["GET", "POST"])
@permission_required('class_recipes')
def recipe_edit(class_id):

    if not class_id:
        class_id = request.args.get('id')

    def recipes(class_id):
        try:
            cls, recipe_set = db.session.query(models.Class, models.RecipeSet)\
                .outerjoin(models.RecipeSet)\
                .filter(models.Class.id == class_id)\
                .one()
        except NoResultFound:
            abort(404)
        if recipe_set is None:
            recipe_set = models.RecipeSet()
            recipe_set.cls = cls
        return cls, recipe_set

    cls, recipe_set = recipes(class_id)
    set_form = forms.RecipeSetForm(request.form, recipe_set)
    set_form.class_name.data = cls.title

    if request.method == 'GET':
        if not active_user().can_view("class_recipes"):
            abort(403)

        recipe_forms = [forms.RecipeForm(obj=recipe, prefix="{}-".format(i))
                        for i, recipe in enumerate(recipe_set.recipes)]
        recipe_forms.sort(key=lambda x: x.recipe_order.data)

    if request.method == 'POST':
        if not active_user().can_update("class_recipes"):
            abort(403)

        recipe_forms = []
        for i in range(20):
            form = forms.RecipeForm(request.form, prefix=str(i + 1) + '-')
            if form.title.name not in request.form:
                break
            recipe_forms.append(form)
        recipe_forms.sort(key=lambda x: x.recipe_order.data)

        if set_form.validate() and all([form.validate() for form in recipe_forms]):
            db.session.begin(subtransactions=True)
            set_form.populate_obj(recipe_set)
            recipe_set.last_updated = datetime.now()
            db.session.add(recipe_set)

            for recipe in recipe_set.recipes:
                db.session.delete(recipe)
            for recipe_form in recipe_forms:
                recipe = models.Recipe()
                recipe_form.populate_obj(recipe)
                recipe.set = recipe_set
                recipe.order = recipe_form.recipe_order.data
                db.session.add(recipe)
            recipe_set.last_updated = datetime.now()
            db.session.commit()

            if 'save' in request.form:
                return redirect(url_for(".recipe_list"))
            set_form.last_updated.data = recipe_set.last_updated
            return render_template("/admin/recipe_edit.html", set_form=set_form,
                                   recipe_forms=recipe_forms, class_id=class_id,
                                   blank_recipe_form=forms.RecipeForm(data={}))

    return render_template("/admin/recipe_edit.html", set_form=set_form,
                           recipe_forms=recipe_forms, class_id=class_id,
                           blank_recipe_form=forms.RecipeForm(data={}))


@blueprint.route("/setup/edit/<int:id>", methods=["GET", "POST"])
@csrf.exempt
@permission_required('class_setups')
def setup_edit(id):
    cls = models.Class.query.get_or_404(id)
    setup = db.session.query(models.Setup).get(id)
    setup_form = forms.SetupForm.new(request.form, setup)
    if setup is None:
        setup = models.Setup()
    setup_form.class_name.data = cls.title

    if setup_form.validate_on_submit() \
            and active_user().can_update("class_setups"):
        db.session.begin(subtransactions=True)
        setup_form.populate_obj(setup)
        setup.last_updated = datetime.now()
        db.session.add(setup)
        setup.id = id
        setup.rounds = []
        for round_form in setup_form.rounds:
            round = models.SetupRound()
            db.session.add(round)
            round_form.populate_obj(round)
            round.points = []
            for point_form in round_form.points:
                point = models.SetupRoundPoint()
                db.session.add(point)
                point_form.populate_obj(point)
                round.points.append(point)
            setup.rounds.append(round)
        if 'clean' in request.form:
            setup.clean_text()
        db.session.commit()

        if 'save' in request.form:
            return redirect(url_for(".setup_list"))
        else:
            return redirect(url_for(".setup_edit", id=id))

    return render_template(
        "/admin/setup_edit.html",
        id=setup.id,
        setup_form=setup_form,
        blank_round_form=forms.SetupRoundForm.from_nothing(),
        blank_point_form=forms.SetupRoundPointForm(data={})
    )

@blueprint.route("/setup/preview/<int:id>")
@permission_required('class_setups')
def setup_preview(id):
    setup = models.Setup.query.get_or_404(id)
    return render_template("/admin/setup_preview.html", setup=setup)

@blueprint.route("/recipes/preview/<int:id>")
@permission_required('class_recipes')
def recipe_preview(id):
    env = utils.nonHTMLJinjaEnv()
    try:
        cls, recipe_set = db.session.query(models.Class, models.RecipeSet)\
            .outerjoin(models.RecipeSet)\
            .filter(models.Class.id == id)\
            .one()
    except NoResultFound:
        abort(404)
    if recipe_set is None:
        recipe_set = models.RecipeSet()
        recipe_set.cls = cls

    header_image = utils.base_64_encoded_file('static/img/printheadergraphic.png')

    return env.get_template("/recipe_preview.html").render(recipe_set=recipe_set,
                                                           cls=cls,
                                                           header_image=header_image)

@blueprint.route("/class/shoppinglists")
@blueprint.route("/class/shoppinglists/<int:page>")
@permission_required('class_shoplists')
def class_shopping_list_list(page=1):
    query = db.session.query(models.ShoppingList).join(models.Class).order_by(models.Class.abbr.asc())
    shopping_lists = create_admin_list(
        query,
        page,
        args=request.args,
        show_all=True
    )
    return render_template("/admin/class_shoppinglist_list.html",
                           pagination=shopping_lists)

@blueprint.route("/shoppinglists/goshopping/<int:class_id>")
@permission_required('class_shoplists')
def go_shopping_for_class(class_id):
    campus_id = session["campus_ids"][0]
    cls = models.Class.query.get_or_404(class_id)
    quantity = 1
    form_name = cls.abbr

    list_instance = models.ShoppingListInstance.create_list_instance(
        active_user_id(),
        form_name,
        [(campus_id, cls.id, quantity)],
    )

    return redirect(url_for(".shopping_list_checklist", id=list_instance.id))


@blueprint.route("/shoppinglists/edit/<int:id>", methods=["GET", "POST"])
@permission_required('class_shoplists')
def shopping_list_edit(id):
    slist = db.session.query(models.ShoppingList).get(id)
    if slist is None:
        slist = models.ShoppingList(id=id)

    cls = db.session.query(models.Class).get(id)
    form = forms.ShoppingListForm(request.form, slist)
    if form.validate_on_submit() and active_user().can_update("class_shoplists"):
        categories = request.form.getlist("item_categories")
        nums = request.form.getlist("item_nums")
        units = request.form.getlist("item_units")
        names = request.form.getlist("item_names")
        markets = request.form.getlist("item_markets")
        notes = request.form.getlist("item_notes")
        form.populate_obj(slist)
        slist.last_updated = datetime.now()
        db.session.begin(subtransactions=True)
        db.session.add(slist)
        for item in slist.items:
            item.active = False

        for category, num, unit, name, market, note in zip(categories, nums, units, names, markets, notes):
            sli = models.ShoppingListItem(number=num, unit=unit, name=name, market=market, notes=note, category=category)
            slist.items.append(sli)
        db.session.commit()

        if 'save' in request.form:
            return redirect(url_for(".class_shopping_list_list"))
        return redirect(url_for(".shopping_list_edit", id=id))

    return render_template("/admin/shoppinglist_edit.html",
                            form=form, cls=cls,
                            slist=slist, shoppinglist_categories=models.ShoppingListItem.CATEGORIES)


@blueprint.route("/shoppinglists/view/<int:id>", methods=["GET"])
@permission_required("class_shoplists")
def shopping_list_view(id):
    slist = db.session.query(models.ShoppingList).get(id)
    cls = db.session.query(models.Class).get(id)

    category_items = {}
    for k, v in models.ShoppingListItem.CATEGORIES.items():
        category_items[k] = {"name": v, "shop_items": []}

    for item in slist.category_ordered_items:
        category_items[item.category]["shop_items"].append(item)

    return render_template("/admin/shoppinglist_viewsingle.html",
                            cls=cls,
                            slist=slist, items=category_items)


@blueprint.route("/shoppinglists/new", methods=["GET", "POST"])
@csrf.exempt
@permission_required("shoplist_generate")
def shopping_list_create():
    if not active_user().can_update("shoplist_generate"):
        abort(403)

    if request.method == "GET":
        user_campuses = db.session.query(models.Campus)\
            .join(models.TeacherCampus)\
            .join(models.Teacher)\
            .filter_by(user_id=active_user_id())

        classes = models.Class.query\
            .join(models.ShoppingList)\
            .order_by(models.Class.abbr)\
            .all()

        current_campus = get_current_campus()

        return render_template("/admin/shoppinglists.html", classes=classes, campuses=user_campuses, current_campus=current_campus)
    else:
        campuses = request.form.getlist("campuses")
        classes = request.form.getlist("classes")
        qtys = request.form.getlist("qtys")
        form_name = request.form.get("name")

        list_instance = models.ShoppingListInstance.create_list_instance(
            active_user_id(),
            form_name if form_name else "Untitled",
            zip(campuses, classes, qtys),
        )

        return redirect(
            url_for(".shopping_list_checklist", id=list_instance.id))


@blueprint.route("/shoppinglists/generate/<id>", methods=["GET", "POST"])
@csrf.exempt
@permission_required("shoplist_generate")
def shopping_list_checklist(id):
    if not active_user().can_update("shoplist_generate"):
        abort(403)

    shopping_list = models.ShoppingListInstance.query.get(id)

    if request.method == "POST":

        if "merge-lists" in request.form:
            campuses = request.form.getlist("campuses-merge")
            classes = request.form.getlist("classes-merge")
            qtys = request.form.getlist("qtys-merge")
            shopping_list.merge_lists(zip(campuses, classes, qtys))
            return redirect(url_for(".shopping_list_checklist", id=shopping_list.id))

        if 'by-store' in request.form:
            stores = request.form.getlist("by_store")
            new_sl = models.ShoppingListInstance\
                           .create_list_instance_by_store(active_user().id,
                                                          shopping_list,
                                                          request.form['by_store_name'],
                                                          stores)
            return redirect(url_for(".shopping_list_checklist", id=new_sl.id))

        if "go_shopping" in request.form:
            return redirect(url_for(".shopping_list_list"))

        ids = request.form.getlist("item_ids")
        nums = request.form.getlist("item_nums")
        units = request.form.getlist("item_units")
        names = request.form.getlist("item_names")
        markets = request.form.getlist("item_markets")
        notes = request.form.getlist("item_notes")
        gotits = request.form.getlist("item_gotits")

        new_campuses = request.form.getlist("new_item_campus")
        new_classes = request.form.getlist("new_item_class")
        new_categories = request.form.getlist("new_item_category")
        new_names = request.form.getlist("new_item_name")
        new_quantities = request.form.getlist("new_item_qty")
        new_units = request.form.getlist("new_item_unit")
        new_notes = request.form.getlist("new_item_notes")
        new_markets = request.form.getlist("new_item_market")
        new_gotits = request.form.getlist("new_item_gotit")

        db.session.begin()
        for campus, item_class, category, name, qty, unit, note, market, gotit in\
                izip_longest(new_campuses, new_classes, new_categories, new_names,
                    new_quantities, new_units, new_notes, new_markets, new_gotits):
            if not gotit:
                form = forms.ShoppingListInstanceItemForm(campus=models.Campus.query.get(campus),
                                                          item_class=item_class,
                                                          category=category,
                                                          quantity=qty,
                                                          csrf_enabled=False)
                form.market.data = market
                form.name.data = name
                form.notes.data = note
                form.unit.data = unit
                if form.validate_on_submit():
                    new_instance_item = models.ShoppingListInstanceItem(shopping_list_instance_id=shopping_list.id,
                                                                        campus_id=int(campus),
                                                                        number=qty,
                                                                        unit=unit,
                                                                        name=name,
                                                                        market=market,
                                                                        notes=note,
                                                                        class_id=item_class or None,
                                                                        is_one_off_item=True,
                                                                        category=category or None)
                    db.session.add(new_instance_item)

        for id, num, unit, name, market, note, got_it in zip(ids, nums, units, names, markets, notes, gotits):
            item = models.ShoppingListInstanceItem.query.get(id)
            item.number = num
            item.unit = unit
            item.name = name
            item.market = market
            item.notes = note
            item.got_it = True if got_it == "1" else False
            db.session.merge(item)
            if "remove_gotits" in request.form and item.got_it:
                for oi in item.original_items:
                    db.session.delete(oi)
                db.session.delete(item)
        shopping_list.last_updated = datetime.utcnow()
        db.session.add(shopping_list)
        db.session.commit()

        if "save" in request.form:
            return redirect(url_for(".shopping_list_checklist", id=shopping_list.id))
        else:
            return redirect(url_for(".shopping_list_display", id=shopping_list.id))

    current_campus = get_current_campus()
    campuses = db.session.query(models.Campus)\
                .join(models.TeacherCampus)\
                .join(models.Teacher)\
                .order_by(models.Campus.name)\
                .filter_by(user_id=active_user_id())\
                .all()

    class_query = models.Class.query.order_by(models.Class.abbr)
    classes = class_query.all()
    classes_with_lists = class_query.join(models.ShoppingList).all()

    #markets = []
    #for item in sorted(shopping_list.aggregated_items, key=attrgetter("category_str", "name")):
    #    market = "Other" if item.market == "" else item.market
    #    markets.append(market)
    #markets = set(markets)

    return render_template("/admin/shoppinglist_checklist.html",
                           shopping_list=shopping_list,
                           campuses=campuses,
                           classes=classes,
                           classes_with_lists=classes_with_lists,
                           current_campus=current_campus,
                           shoppinglist_categories=models.ShoppingListItem.CATEGORIES)
                           #markets=markets)


@blueprint.route("/shoppinglists/display/<id>", methods=["GET"])
@permission_required("shoplist_shop")
def shopping_list_display(id):

    list_instance = db.session.query(models.ShoppingListInstance).get(id)

    market_items = {}
    for item in sorted(list_instance.aggregated_items, key=attrgetter("category_str", "name")):
        market = "Other" if item.market == "" else item.market
        if item.market not in market_items:
            market_items[item.market] = []
        market_items[item.market].append(item)

    markets = market_items.keys()

    market_ids = {}
    for market in markets:
        market_id = market
        for char in (' ', '"', "'"):
            market_id = market_id.replace(char, '_')
        market_ids[market] = market_id

    return render_template("/admin/shoppinglist_display.html",
                            shopping_list=list_instance,
                            visible_items=market_items,
                            market_ids=market_ids,
                            markets=markets)


@blueprint.route("/shoppinglists", methods=["GET"])
@permission_required("shoplist")
def shopping_list_list():
    query = db.session.query(
                            models.ShoppingListInstance,
                            models.User,
                            func.group_concat(models.Campus.name),
                            func.group_concat(models.Campus.abbreviation)
            )\
            .select_from(models.ShoppingListInstance)\
            .join(models.User)\
            .join(models.ShoppingListInstanceItem)\
            .join(models.Campus, models.Campus.id == models.ShoppingListInstanceItem.campus_id)\
            .group_by(models.ShoppingListInstance.id)\
            .order_by(models.ShoppingListInstance.created.desc())\
            .filter(
                models.ShoppingListInstance.created > datetime.now() - timedelta(days=30),
                models.ShoppingListInstance.active == True
            )

    return render_template("/admin/shoppinglist_list.html", items=query)


@blueprint.route("/shoppinglists/delete", methods=["POST"])
@csrf.exempt
@permission_required("shoplist_delete")
def shopping_list_delete():
    if not active_user().can_update("shoplist_delete"):
        abort(403)

    id = request.form.get("id")
    db.session.begin()
    list_instance = db.session.query(models.ShoppingListInstance).get(id)
    list_instance.active = False
    db.session.merge(list_instance)
    db.session.commit()

    return redirect(url_for(".shopping_list_list"))


@blueprint.route("/shoppinglists", methods=["GET"])
@blueprint.route("/shoppinglists/checkin/<id>", methods=["GET", "POST"])
@csrf.exempt
@permission_required("shoplist_check")
def shopping_list_checkin(id):
    shopping_list = models.ShoppingListInstance.query.get(id)

    if request.method == "POST":
        if "go_shopping" in request.form:
            return redirect(url_for(".shopping_list_list"))

        if not active_user().can_update("shoplist_check"):
            abort(403)

        checkins = set([int(checkin) for checkin in request.form.getlist("checkins")])
        ids = request.form.getlist("item_id")
        qty = request.form.getlist("qty")

        item_quantities = {}
        for item_id, item_qty in zip(ids, qty):
            item_quantities[int(item_id)] = item_qty

        db.session.begin()
        for item in shopping_list.items:

            if item_quantities[item.id] != item.number:
                item.number = item_quantities[item.id]
                if item.original_items:
                    original_item = item.original_items[0].shopping_list_item
                    original_item.number = item_quantities[item.id]
                    db.session.query(original_item)

            item.checked_in = (item.id in checkins)
            db.session.merge(item)
            if "remove_checkins" in request.form and item.checked_in:
                for oi in item.original_items:
                    db.session.delete(oi)
                db.session.delete(item)

        shopping_list.last_updated = datetime.now()
        db.session.add(shopping_list)
        db.session.commit()

        if "remove_checkins" in request.form:
            return redirect(url_for(".shopping_list_checkin", id=shopping_list.id))
        else:
            return redirect(url_for(".dashboard"))

    return render_template("/admin/shoppinglist_checkin.html",
                shopping_list=shopping_list,
                items=sorted(shopping_list.items, key=attrgetter("category_str", "name", "campus.name"))
    )


@blueprint.route("/preprep_list", methods=["GET"])
@permission_required("preprep")
def preprep_list_list():
    query = db.session.query(
                            models.PrePrepList,
                            models.User,
            )\
            .join(models.User)\
            .group_by(models.PrePrepList.id)\
            .order_by(models.PrePrepList.created.desc())\
            .filter(
                models.PrePrepList.active == True
            ).all()
    results = []
    for tup in query:
        classes = db.session.query(models.Class).join(models.Setup).join(models.PrePrepListItem)\
                            .filter(models.PrePrepListItem.pre_prep_list_id==tup[0].id)\
                            .all()
        row = list(tup)
        row.append(classes)
        results.append(row)

    return render_template("/admin/preprep_list_list.html", items=results)


@blueprint.route("/preprep_list_create", methods=["GET", "POST"])
@permission_required("preprep_generate")
def preprep_list_create():
    if not active_user().can_update("preprep_generate"):
        abort(403)

    if request.method == "GET":

        classes = models.Class.query\
            .join(models.Setup)\
            .order_by(models.Class.abbr)\
            .all()

        return render_template("/admin/preprep_list_create.html", classes=classes)
    else:
        name = request.form.get("name", "Untitled")
        classes = request.form.getlist("classes")

        list_instance = models.PrePrepList.create_list_instance(active_user_id(), name, classes)

        return redirect(
            url_for(".preprep_list_edit", preprep_id=list_instance.id))


@blueprint.route("/preprep_list_edit/<int:preprep_id>", methods=["GET", "POST"])
@permission_required("preprep_edit")
def preprep_list_edit(preprep_id):
    preprep_list = db.session.query(models.PrePrepList).get(preprep_id)
    if request.method == "GET":
        return render_template("/admin/preprep_list_edit.html", preprep_list=preprep_list)
    else:
        db.session.begin()
        preprep_list.name = request.form.get('name', 'Untitled')
        db.session.add(preprep_list)

        for field in request.form:
            if 'text' in field:
                item_id = field.split('_')[1]
                item = db.session.query(models.PrePrepListItem).get(int(item_id))
                item.text = request.form[field]
                db.session.add(item)
        db.session.commit()

        if 'save_and_continue' in request.form:
            return render_template("/admin/preprep_list_edit.html", preprep_list=preprep_list)
        else:
            return redirect(url_for(".preprep_list_list"))


@blueprint.route("/preprep_list_delete/<int:preprep_id>")
@permission_required("preprep_delete")
def preprep_list_delete(preprep_id):
    db.session.begin()
    preprep = db.session.query(models.PrePrepList).filter(models.PrePrepList.id==preprep_id).first()
    db.session.delete(preprep)
    db.session.commit()
    return redirect(url_for(".preprep_list_list"))


@blueprint.route("/preprep_preview/<int:preprep_id>")
def preprep_preview(preprep_id):
    preprep_list = db.session.query(models.PrePrepList).get(preprep_id)
    return render_template("/admin/preprep_preview.html", preprep_list=preprep_list)


@blueprint.route("/newsletter_subscribers", methods=["GET"])
@blueprint.route("/newsletter_subscribers/<int:page>", methods=["GET"])
@permission_required("subscriber_list")
def subscriber_list(page=1):
    search_query = request.args.get("q", "")

    query = models.Subscriber.query.filter(models.Subscriber.active == True)
    if search_query:
        query = query.filter(or_(
                        models.Subscriber.email.like("%{}%".format(search_query)),
                        models.Subscriber.name.like("%{}%".format(search_query)),
                    )
                )

    subscribers = create_admin_list(
        query,
        page,
        request.args,
        sorters=sorting.subscriber_criteria,
        per_page=100
    )

    return render_template("/admin/subscriber_list.html", pagination=subscribers)


@blueprint.route("/newsletter_subscriber/new", methods=["GET", "POST"])
@blueprint.route("/newsletter_subscriber/edit/<id>", methods=["GET", "POST"])
@permission_required("subscriber_list")
def subscriber_edit(id=None):
    if id is not None:
        subscriber = db.session.query(models.Subscriber).get(id)
    else:
        subscriber = models.Subscriber()
    form = forms.SubscriberEditForm(request.form, obj=subscriber)
    form.subscribe_reason.data = subscriber.readable_subscribe_reason
    if form.validate_on_submit() and active_user().can_update("subscriber_list"):
        old_subscriber = db.session.query(models.Subscriber)\
            .filter(models.Subscriber.email == form.email.data, models.Subscriber.id != id)\
            .scalar()
        if old_subscriber and old_subscriber.active:
            form.email.errors.append(
                "This email address is already subscribed")
        else:
            if old_subscriber:
                db.session.delete(old_subscriber)
            db.session.begin(subtransactions=True)
            form.populate_obj(subscriber)
            subscriber.subscribe_reason = 'admin_registered'
            db.session.merge(subscriber)
            db.session.commit()
            return redirect(url_for(".subscriber_list"))
    return render_template(
        "/admin/subscriber_edit.html", subscriber=subscriber, form=form)

@csrf.exempt
@blueprint.route("/newsletter_subscriber/delete", methods=["POST"])
@permission_required("subscriber_list")
def subscriber_delete():
    if not active_user().can_update("subscriber_list"):
        abort(403)

    ids_to_delete = request.form.getlist("ids")
    db.session.begin(subtransactions=True)
    for id in ids_to_delete:
        obj = db.session.query(models.Subscriber).get(id)
        if obj:
            obj.active = False
        db.session.add(obj)
    db.session.commit()
    return redirect(url_for(".subscriber_list"))


@blueprint.route("/newsletter_subscriber/subscriber_export.csv", methods=["GET"])
@permission_required("subscriber_list")
def subscriber_export():
    query = db.session.query(
                    models.Subscriber,
                    models.Campus.name.label("campus_name"),
                )\
                .select_from(models.Subscriber)\
                .outerjoin(models.Campus)\
                .filter(models.Subscriber.active == True)

    def generate_rows():
        yield ["Name", "Email", "Studio Name", "Subscribe Reason"]
        for subscriber, campus_name in query:
            yield [subscriber.email, subscriber.name, campus_name,
                   subscriber.subscribe_reason]

    return Response(utils.csv_from_rows(generate_rows()), mimetype="text/csv")

@blueprint.route("/products", methods=["GET"])
@blueprint.route("/products/<int:page>", methods=["GET"])
@permission_required("product")
def product_list(page=1):
    search_query = request.args.get("q", "")

    query = models.Product.query.filter(models.Product.active == True)
    if search_query:
        query = query.filter(or_(
            models.Product.name.like("%{}%".format(search_query)),
            models.Product.type.like("%{}%".format(search_query)),
        ))

    products = create_admin_list(
        query,
        page,
        request.args,
        sorters=sorting.product_criteria,
        default_column="order",
        default_order="asc",
        per_page=50
    )

    return render_template("/admin/product_list.html", pagination=products)

@csrf.exempt
@blueprint.route("/product/delete", methods=["POST"])
@permission_required("product")
def product_delete():
    if not active_user().can_update("product"):
        abort(403)

    ids = request.form.getlist("products")
    db.session.begin(subtransactions=True)
    for id in ids:
        obj = db.session.query(models.Product).get(id)
        if obj:
            obj.active = False
        db.session.add(obj)
    db.session.commit()
    return redirect(url_for(".product_list"))

@blueprint.route("/product/new", methods=["GET", "POST"])
@blueprint.route("/product/edit/<id>", methods=["GET", "POST"])
@permission_required("product")
def product_edit(id=None):
    if id is None:
        product = models.Product()
    else:
        product = db.session.query(models.Product).get(id)

    form = forms.ProductEditForm(request.form, obj=product)
    if request.form and form.validate() and active_user().can_update("product"):
        form.name.data = form.name.data.strip()
        form.populate_obj(product)
        db.session.begin(subtransactions=True)
        db.session.add(product)
        if request.files.get(form.image.name):
            upload_photo = request.files[form.image.name]
            product.photo = models.ClassPhoto(photo='')
            db.session.flush()
            photo_file = utils.file_upload(
                upload_photo, product.base_name, models.Product.image_dir)
            product.photo.photo = photo_file
        if request.files.get(form.thumbnail_image.name):
            # thumbnail_photo_file = utils.file_upload(
            #     thumbnail_photo, base_name, "thumbnails")
            thumbnail_photo = request.files[form.thumbnail_image.name]
            utils.create_thumbnail(thumbnail_photo, product.base_name)

        db.session.commit()
        return redirect(url_for(".product_list"))
    return render_template(
        "/admin/product_edit.html", product=product, form=form)


@blueprint.route("/teacher/sales", methods=["GET", "POST"])
@permission_required("make_sale")
def teacher_sales():
    campus_ids = session.get("campus_ids", ())
    user = active_user()
    form = forms.TeacherSalesOrderForm.new(
        campus_ids, request.form, sold_by=user)
    admin_cart = cart.ShoppingCart(session, key="sales-shopping-cart")

    max_row = db.session.query(func.max(models.Product.row))\
            .select_from(models.Product)\
            .join(models.ProductInventory)\
            .filter(
                models.ProductInventory.active == True,
                models.ProductInventory.campus_id.in_(campus_ids)
            ).scalar()
    grid = [[None] * 4 for r in range(0, 0 if max_row is None else max_row)]

    products = db.session.query(models.Product)\
            .select_from(models.Product)\
            .join(models.ProductInventory)\
            .filter(
                models.Product.row > 0,
                models.Product.column > 0,
                models.Product.column <= 4,
                or_(
                    models.Product.splash_type == True,
                    models.Product.type == "",
                ),
                models.ProductInventory.active == True,
                models.ProductInventory.campus_id.in_(campus_ids)
            )\
            .order_by(models.Product.row, models.Product.column)

    for product in products:
        if grid[product.row - 1][product.column - 1] is None:
            grid[product.row - 1][product.column - 1] = product

    if session.get('sales-data') and session['sales-data'].get('studio_id'):
        form.studio.data = models.Campus.query.get(session["sales-data"]['studio_id'])
    else:
        default_studio = form.studio.query.first()
        session["sales-data"] = {}
        session["sales-data"]['studio_id'] = default_studio.id
        form.studio.data = models.Campus.query.get(session["sales-data"]['studio_id'])

    if form.validate_on_submit() and admin_cart.products:
        quantity_fields = {k: v for k, v in request.form.iteritems() if 'product_quantity' in k}
        for field, qty in quantity_fields.iteritems():
            product_id = field.split('_')[2]
            admin_cart.update_product_quantities([(product_id, int(qty))])

        admin_cart.product_discount_percent = form.discount.data
        admin_cart.pickup = True
        sales_data = {
            "studio_id": form.studio.data.id,
            "discount": form.discount.data,
            "sold_by_id": form.sold_by.data.id,
            "paid_with": form.paid_with.data,
        }
        session["sales-data"] = sales_data
        if 'update' in request.form:
            return redirect(url_for(".teacher_sales"))
        elif 'ring_up' in request.form:
            return redirect(url_for(".teacher_sales_ring_up"))

    return render_template("/admin/teacher_sales.html", product_grid=grid,
                           form=form, cart=admin_cart)
    #return str(form.studio.data.id)


@blueprint.route("/teacher/sales/product/<int:product_id>", methods=["GET", "POST"])
@permission_required("make_sale")
def teacher_sales_product(product_id):
    product = db.session.query(models.Product).get(product_id)
    related_products = db.session.query(models.Product)\
        .filter(models.Product.name == product.name)
    if product is None:
        abort(404)
    studio = db.session.query(models.Campus).get(session["sales-data"]['studio_id'])
    stock = models.ProductInventory.stocked(studio.id, product_id)
    #sold = models.ProductOrderItem.sold(studio.id, product_id)

    shopping_cart = cart.ShoppingCart(session, key="sales-shopping-cart")

    form = forms.StoreProductForm()
    if request.method == "POST":
        if form.validate_with_quantity(stock):
            shopping_cart.update_product_quantities([(form.selected_product_id.data, form.quantity.data)])
        return redirect(url_for(".teacher_sales"))
    return render_template("/admin/teacher_product.html", product=product,
                           remaining=stock, form=form,
                           related_products=related_products)


@blueprint.route("/teacher/sales/product-details-json/")
def sales_product_details():
    product_id = request.args["id"]
    product = models.Product.query.get_or_404(product_id)
    return jsonify(
        selected_product_id=product.id,
        type=product.type,
        image_url=product.url,
        price=format(product.price, "0.2f"),
        description=product.description,
        quantity=product.remaining(session["sales-data"]['studio_id']),
        )


@blueprint.route("/teacher/sales/check-studio/")
def sales_check_studio():
    studio_id = request.args["id"]
    studio = models.Campus.query.get_or_404(studio_id)

    if session.get('sales-data') and session['sales-data'].get('studio_id'):
        if studio.id != int(session["sales-data"]['studio_id']):
            shopping_cart = cart.ShoppingCart(session, key="sales-shopping-cart")
            shopping_cart.empty()
            session['sales-data'] = {}
            session['sales-data']['studio_id'] = studio.id
            return jsonify(changed=True)
    return jsonify(changed=False)


@blueprint.route("/teacher/sales/totals", methods=["POST"])
@permission_required("make_sale")
def teacher_sales_totals():
    campus_ids = session.get("campus_ids", ())
    sale_info_form = forms.TeacherSalesOrderForm.new(campus_ids, sold_by=active_user())
    if not sale_info_form.validate():
        abort(500)

    product_quantities = get_product_quantities(request.form)
    studio = sale_info_form.studio.data
    admin_cart = cart.ShoppingCart(session, studio,
                                   key="sales-shopping-cart")
    admin_cart.product_discount_percent = sale_info_form.discount.data
    admin_cart.pickup = True
    admin_cart.update_product_quantities(product_quantities)

    return jsonify(
        items=admin_cart.product_count,
        amount=format(admin_cart.product_subtotal, "0.2f"),
        tax=format(admin_cart.product_tax, "0.2f"),
        discount=format(admin_cart.product_discount, "0.2f"),
        total=format(admin_cart.product_total, "0.2f"),
    )


@blueprint.route("/teacher/sales/ring-up", methods=["GET", "POST"])
@permission_required("make_sale")
def teacher_sales_ring_up():
    sales_data = session["sales-data"]
    studio = models.Campus.query.get_or_404(sales_data["studio_id"])
    admin_cart = cart.ShoppingCart(
        session, studio, key="sales-shopping-cart")
    print session[admin_cart.key], admin_cart.product_discount_percent

    if request.form and admin_cart.product_total \
            and active_user().can_update("make_sale"):
        db.session.begin()
        purchase = models.Purchase(
            timestamp=datetime.now(),
            ip_address="",
            first_name="",
            last_name="",
            email="IN STORE",
            amount=admin_cart.product_total,
            authorization_code="NONE",
            user_id=sales_data["sold_by_id"],
        )
        db.session.add(purchase)
        db.session.flush()
        transaction = models.Transaction(
            purchase_id=purchase.id,
            payment_method=sales_data["paid_with"],
            amount=admin_cart.product_total,
        )
        db.session.add(transaction)
        order = models.ProductOrder(
            campus_id=studio.id,
            sold_by_id=sales_data["sold_by_id"],
            purchase_id=purchase.id,
            online_sale=False,
            in_store_pickup=admin_cart.pickup_state,
            paid_with=sales_data["paid_with"],
            discount=sales_data["discount"],
            date_ordered=datetime.now(),
        )
        db.session.add(order)
        order.assign_products(
            studio, admin_cart.products, in_store_pickup=True,
            discount=admin_cart.product_discount_percent)
        db.session.commit()
        session.pop("sales-data", None)
        return redirect(url_for(".teacher_sales_complete"))

    return render_template(
        "/admin/teacher_sales_ring_up.html",
        products=admin_cart.products,
        amount=format(admin_cart.product_subtotal, "0.2f"),
        tax=format(admin_cart.product_tax, "0.2f"),
        discount=format(admin_cart.product_discount, "0.2f"),
        total=format(admin_cart.product_total, "0.2f"),
    )

def get_product_quantities(formdata):
    product_quantities = {}
    for name, quantity in formdata.iteritems():
        match = re.match("product-(\d+)", name)
        if match is not None and re.match("^\d+$", quantity) is not None:
            product_id = match.group(1)
            product_quantities[product_id] = int(quantity)
    return product_quantities


@blueprint.route("/teacher/sales/complete")
@permission_required("make_sale")
def teacher_sales_complete():
    shopping_cart = cart.ShoppingCart(session, key="sales-shopping-cart")
    shopping_cart.empty()
    return render_template("/admin/teacher_sales_complete.html")


@csrf.exempt
@blueprint.route("/save_note", methods=["POST"])
@admin_required
def save_note():
    if not active_user().is_superuser:
        abort(403)
    note = models.AdminNote(
                user_id=active_user_id(),
                note=request.form.get("note", "")
            )
    db.session.begin()
    db.session.add(note)
    db.session.commit()
    return redirect(url_for(".dashboard"))

@blueprint.route("/reports")
@permission_required("reports")
def reports():
    return render_template("/admin/reports.html")


class ReportView(MethodView):
    decorators = [admin_required]

    form_class = NotImplemented
    template = NotImplemented
    filename = NotImplemented

    def form(self, *args, **kwargs):
        form = self.form_class(*args, **kwargs)
        form.request_form = request.form
        form.studio.query = db.session.query(models.Campus)\
            .join(models.TeacherCampus)\
            .join(models.Teacher)\
            .filter_by(user_id=active_user_id())\
            .distinct()
        return form

    def get(self):
        if not active_user().can_view("reports"):
            abort(403)

        return render_template(self.template, form=self.form())

    def post(self):
        if not active_user().can_view("reports"):
            abort(403)
        form = self.form()
        if form.validate_on_submit():
            report_body = self.generate_report(form)
            response = make_response(report_body)
            response.headers.add("Content-Disposition", "attachment",
                                 filename=self.filename)
            return response
        return render_template(self.template, form=form)

    def generate_report(self, form):
        raise NotImplementedError

    @classmethod
    def register_view(cls, name, route):
        view = cls.as_view(name)
        blueprint.add_url_rule(route, view_func=view)
        return view


class GiftCertificateReport(ReportView):
    form_class = forms.ReportGiftCertForm
    template = "/admin/reports_gift_cert.html"
    filename = "gift-certificate-report.csv"

    def generate_report(self, form):
        categories = []
        if form.filter.data == forms.ReportGiftCertForm.FILTER_PURCHASED:
            categories = models.GiftCertificate.CATEGORIES_PURCHASED
        elif form.filter.data == forms.ReportGiftCertForm.FILTER_MAKEUP:
            categories = [models.GiftCertificate.CATEGORY_MAKEUP]
        elif form.filter.data != forms.ReportGiftCertForm.FILTER_ALL:
            categories = [form.paid_with.data]

        return gift_certificate_report(form.studio.data, categories, *form.date.dates)

GiftCertificateReport.register_view(
    'reports_gift_cert', "/reports/gift-certificate")


class NumberOfEventsReport(ReportView):
    form_class = forms.MultipleStudioReportForm
    template = "/admin/reports_number_of_events.html"
    filename = "number_of_events_report.csv"

    def generate_report(self, form):
        return number_of_events_report(form.studio.data, *form.date.dates)

NumberOfEventsReport.register_view(
    'reports_number_of_events', "/reports/number-of-events")


class ClassesAndOccupancyReport(ReportView):
    form_class = forms.PlainReportForm
    template = "/admin/reports_classes_and_occupancy.html"
    filename = "number_of_classes_and_occupancy_rates.csv"

    def generate_report(self, form):
        return classes_and_occupancy_report(form.studio.data, *form.date.dates)

ClassesAndOccupancyReport.register_view(
    'reports_classes_and_occupancy', "/reports/classes-and-occupancy")


class PrivateClassReport(ReportView):
    form_class = forms.MultipleStudioReportForm
    template = "/admin/reports_private_class.html"
    filename = "private-class.csv"

    def generate_report(self, form):
        return private_class_report(form.studio.data, *form.date.dates)

PrivateClassReport.register_view(
    'reports_private_class', "/reports/private-class")


class ClassesTaughtReport(ReportView):
    form_class = forms.ClassesTaughtReportForm
    template = "/admin/reports_classes_taught.html"
    filename = "classes-taught.csv"

    def generate_report(self, form):
        return classes_taught_report(
            form.cls.data, form.studio.data, *form.date.dates)

ClassesTaughtReport.register_view(
    'reports_classes_taught', "/reports/classes-taught")


class NewsletterSubscribersReport(ReportView):
    form_class = forms.NewsletterSubscribersReportForm
    template = "/admin/reports_newsletter_subscribers.html"
    filename = "newsletter_subscribers.csv"

    def generate_report(self, form):
        return newsletter_subscribers_report(form.studio.data, form.reasons.data, *form.date.dates)

NewsletterSubscribersReport.register_view(
    'reports_newsletter_subscribers', "/reports/newsletter-subscribers")


class SchedulePageReport(ReportView):
    form_class = forms.SchedulePageReportForm
    template = "/admin/reports_schedule_page.html"
    filename = "schedule-page.csv"

    def generate_report(self, form):
        return schedule_page_report(
            form.teacher.data, form.studio.data, *form.date.dates)

SchedulePageReport.register_view(
    'reports_schedule_page', "/reports/schedule-page")


class SalesReport(ReportView):
    form_class = forms.SalesReportForm
    template = "/admin/reports_sales.html"
    filename = "sales.csv"

    def generate_report(self, form):
        return sales_report(form.teacher.data,
                            form.studio.data,
                            form.item.data,
                            *form.date.dates)

SalesReport.register_view('reports_sales', "/reports/sales")


class SalesOfTheDayReport(ReportView):
    form_class = forms.SalesOfTheDayReportForm
    template = "/admin/reports_sales_of_the_day.html"
    filename = "sales-of-the-day.csv"

    def generate_report(self, form):
        return sales_of_the_day_report(
            form.teacher.data, form.studio.data, *form.date.dates)

SalesOfTheDayReport.register_view(
    'reports_sales_of_the_day', "/reports/sales-of-the-day")


class InventoryAdjustmentsReport(ReportView):
    form_class = forms.InventoryAdjustmentsReportForm
    template = "/admin/reports_inventory_adjustments.html"
    filename = "inventory_adjustments.csv"

    def generate_report(self, form):
        return inventory_adjustments_report(form.studio.data,
                                            form.product.data,
                                            form.reason.data,
                                            *form.date.dates)

InventoryAdjustmentsReport.register_view(
    'reports_inventory_adjustments', "/reports/inventory-adjustments")


@blueprint.route("/products/inventory")
@blueprint.route("/products/inventory/<int:page>")
@permission_required("product")
def product_inventory_list(page=1):
    search_query = request.args.get("q", "")
    show_all = (True if request.args.get('show', '') == 'All' else False)

    campus_ids = session.get("campus_ids", [])

    query = db.session.query(models.Campus, models.Product, models.ProductInventory)\
        .select_from(models.Campus)\
        .join(models.Product, literal(1) == 1)\
        .outerjoin(models.ProductInventory, and_(
                models.ProductInventory.product_id == models.Product.id,
                models.ProductInventory.campus_id == models.Campus.id
            )
        )\
        .filter(models.ProductInventory.campus_id.in_(campus_ids))\
        .order_by(models.Product.name.asc())

    def inventory_filters(query, args):
        status = args.get("active", "")
        if status == 'All':
            return query
        elif status == 'True' or not status:
            return query.filter(models.ProductInventory.active == True)
        elif status == 'False':
            return query.filter(models.ProductInventory.active == False)

    product_names_query = db.session.query(models.Product.name)\
                            .outerjoin(models.ProductInventory)\
                            .filter(models.ProductInventory.campus_id.in_(campus_ids))
    product_names_query = crossapply_filters([inventory_filters], product_names_query, request.args)
    product_names = sorted(set([x[0] for x in product_names_query.all()]))

    if request.args.get("show") and not show_all:
        per_page = int(request.args.get('show'))
    else:
        per_page = 100

    inventory = create_admin_list(
        query,
        page,
        request.args,
        sorters=sorting.product_inventory_criteria,
        filters=[inventory_filters, product_name_filters],
        per_page=per_page,
        show_all=show_all
    )

    return render_template("/admin/product_inventory_list.html",
                           pagination=inventory,
                           product_names=product_names)

@blueprint.route("/products/inventory/<campus_id>/<product_id>", methods=["GET", "POST"])
@permission_required("product")
def product_inventory(campus_id, product_id):
    pi = models.ProductInventory.query\
        .filter(
            models.ProductInventory.product_id == product_id,
            models.ProductInventory.campus_id == campus_id
        )\
        .first()

    if pi is None:
        pi = models.ProductInventory(
                campus_id=campus_id,
                product_id=product_id,
                active=True
        )

    pi_item = models.ProductInventoryItem(
                campus_id=campus_id,
                product_id=product_id,
    )

    form = forms.ProductInventoryAdjustForm(request.form, obj=pi_item, pi=pi)
    if form.validate_on_submit() and active_user().can_update("product"):
        db.session.begin(subtransactions=True)

        form.populate_obj(pi_item)
        if not pi_item.quantity:
            pi_item.quantity = 0
        pi_item.blame = active_user_id()

        pi.active = form.active.data
        pi.quantity_to_stock = form.quantity_to_stock.data
        pi.date_stocked = form.date.data
        pi.quantity_stocked = pi.quantity_stocked + pi_item.quantity

        if form.reason.data == "1":  # transferring to another campus
            transfer_campus_pi = models.ProductInventory.query\
                .filter(
                    models.ProductInventory.product_id == product_id,
                    models.ProductInventory.campus_id == form.dest_campus.data.id
                )\
                .first()
            if transfer_campus_pi is None:
                transfer_campus_pi = models.ProductInventory(
                    campus_id=form.dest_campus.data.id,
                    product_id=product_id,
                    active=True
                )
            if transfer_campus_pi.quantity_stocked:
                transfer_campus_pi.quantity_stocked += abs(form.quantity.data)
            else:
                transfer_campus_pi.quantity_stocked = abs(form.quantity.data)

            transfer_pi_item = models.ProductInventoryItem(
                campus_id=form.dest_campus.data.id,
                product_id=product_id,
                blame=active_user_id(),
                reason='Transfer To',
                quantity=abs(form.quantity.data)
            )

            db.session.merge(transfer_campus_pi)
            db.session.add(transfer_pi_item)

        db.session.add(pi_item)
        db.session.merge(pi)

        db.session.commit()
        return redirect(url_for(".product_inventory_list"))
    else:
        form.active.data = pi.active
        form.quantity_to_stock.data = pi.quantity_to_stock

    return render_template("/admin/product_inventory.html", form=form, product_inventory=pi)


@blueprint.route("/products/inventory/new/", methods=["GET", "POST"])
@permission_required("product")
def new_product_inventory():
    form = forms.NewProductInventoryForm(request.form)
    if form.validate_on_submit() and active_user().can_update("product"):
        db.session.begin(subtransactions=True)

        product_inventory_item = models.ProductInventoryItem()
        form.populate_obj(product_inventory_item)
        product_inventory_item.reason = 0

        db.session.add(product_inventory_item)
        db.session.commit()
        return redirect(url_for(".product_inventory_log"))
    return render_template("/admin/new_product_inventory.html", form=form)


@blueprint.route("/products/inventory/edit_log/<campus_id>/<logitem_id>", methods=["GET", "POST"])
@permission_required("product")
def edit_product_inventory_log(campus_id, logitem_id):

    pi_item = db.session.query(models.ProductInventoryItem)\
                .filter(models.ProductInventoryItem.id == logitem_id).one()
    pi = db.session.query(models.ProductInventory)\
        .filter(models.ProductInventory.campus_id == campus_id,
                models.ProductInventory.product_id == pi_item.product_id).one()

    form = forms.ProductInventoryAdjustForm(request.form, obj=pi_item, pi=pi)
    if form.validate_on_submit() and active_user().can_update("product"):
        db.session.begin(subtransactions=True)
        original_reason = pi_item.reason

        form.populate_obj(pi_item)
        pi_item.blame = active_user_id()

        pi.active = form.active.data
        pi.quantity_to_stock = form.quantity_to_stock.data
        pi.date_stocked = form.date.data
        pi.quantity_stocked = pi.quantity_stocked + pi_item.quantity

        if form.reason.data == "1":  # transferring to another campus
            if original_reason == 1:  # original inventory update was a transfer
                flash('You must update the inventory for the other campus(s) to ensure consistency.')
            else:
                transfer_campus_pi = models.ProductInventory.query\
                    .filter(
                        models.ProductInventory.product_id == pi.product_id,
                        models.ProductInventory.campus_id == form.dest_campus.data.id
                    )\
                    .first()
                if transfer_campus_pi is None:
                    transfer_campus_pi = models.ProductInventory(
                        campus_id=form.dest_campus.data.id,
                        product_id=pi.product_id,
                        active=True
                    )
                if transfer_campus_pi.quantity_stocked:
                    transfer_campus_pi.quantity_stocked += abs(form.quantity.data)
                else:
                    transfer_campus_pi.quantity_stocked = abs(form.quantity.data)

                transfer_pi_item = models.ProductInventoryItem(
                    campus_id=form.dest_campus.data.id,
                    product_id=pi.product_id,
                    blame=active_user_id(),
                    reason='Transfer To',
                    quantity=abs(form.quantity.data)
                )

                db.session.merge(transfer_campus_pi)
                db.session.add(transfer_pi_item)

        db.session.merge(pi_item)
        db.session.merge(pi)

        db.session.commit()
        return redirect(url_for(".product_inventory_log"))
    else:
        form.quantity_to_stock.data = pi.quantity_to_stock
        form.reason.data = pi_item.reason
        form.date.data = pi_item.date_stocked
        form.active.data = pi.active

    return render_template("/admin/edit_product_inventory.html", form=form, product_inventory=pi)


@blueprint.route("/products/inventory/log", methods=["GET"])
@blueprint.route("/products/inventory/log/<int:page>")
@permission_required("product")
def product_inventory_log(page=1):

    query = db.session.query(models.ProductInventoryItem, models.Campus, models.Product)\
                .select_from(models.ProductInventoryItem)\
                .join(models.Product)\
                .join(models.Campus, \
                      models.ProductInventoryItem.campus_id == models.Campus.id
                )\
                .filter(models.Campus.id.in_(session.get("campus_ids", [])))\

    campus_ids = session.get("campus_ids", [])
    product_names_query = db.session.query(models.Product.name)\
                            .outerjoin(models.ProductInventory)\
                            .filter(models.ProductInventory.campus_id.in_(campus_ids))
    product_names = sorted(set([x[0] for x in product_names_query.all()]))

    def inventory_filters(query, args):
        return query.filter(models.ProductInventory.active == (False if args.get("active", "True") == "False" else True))

    def date_filters(query, args):
        if args.get('date'):
            if args.get('date') == 'asc':
                return query.order_by(models.ProductInventoryItem.date_stocked.asc())
        return query.order_by(models.ProductInventoryItem.date_stocked.desc())

    inventory = create_admin_list(
        query,
        page,
        request.args,
        sorters=sorting.product_inventory_log_criteria,
        filters=[product_name_filters, date_filters],
        per_page=100
    )

    return render_template("/admin/product_inventory_log.html",
                           pagination=inventory,
                           product_names=product_names)


@csrf.exempt
@blueprint.route("/products/inventory/log/delete", methods=["POST"])
@permission_required("product")
def delete_product_inventory_log():
    if not active_user().can_update("product"):
        abort(403)

    to_delete = request.form.getlist("items_to_delete")

    db.session.begin(subtransactions=True)
    for pi_item in models.ProductInventoryItem.query.filter(
                    models.ProductInventoryItem.id.in_(to_delete)
                ):
        pi = models.ProductInventory.query\
            .filter(
                models.ProductInventory.product_id == pi_item.product_id,
                models.ProductInventory.campus_id == pi_item.campus_id)\
            .first()
        if pi is not None:
            pi.quantity_stocked = pi.quantity_stocked - pi_item.quantity
        db.session.merge(pi)
        db.session.delete(pi_item)
    db.session.commit()

    return redirect(url_for(".product_inventory_log"))


@blueprint.route("/products/inventory/log/inventory_export.csv", methods=["GET"])
@permission_required("product")
def export_product_inventory_log():
    query = db.session.query(models.ProductInventoryItem, models.Campus, models.Product)\
                .select_from(models.ProductInventoryItem)\
                .join(models.Product)\
                .join(models.Campus, \
                      models.ProductInventoryItem.campus_id == models.Campus.id
                )\
                .order_by(models.ProductInventoryItem.date_stocked.desc())

    def generate_rows():
        yield ["Date", "Studio", "Product", "Type", "Adjustment Amount", "Reason"]
        for log_item, campus, product in query:
            yield [
                log_item.date_stocked, campus.name, product.name, product.type,
                log_item.quantity, log_item.reason_str
            ]

    return Response(utils.csv_from_rows(generate_rows()), mimetype="text/csv")


@blueprint.route("/orders")
@blueprint.route("/orders/<int:page>")
@permission_required("schedule")
def order_list(page=1):
    search_query = request.args.get("q", "")

    query = db.session.query(models.ScheduleOrder, models.Purchase)\
                .outerjoin(models.Purchase)\
                .options(joinedload(models.Purchase.gift_certificates))\
                .filter(models.ScheduleOrder.active == True)\
                .order_by(models.ScheduleOrder.created.desc())

    if search_query:
        query = query.filter(or_(
                    models.ScheduleOrder.first_name.like("%{}%".format(search_query)),
                    models.ScheduleOrder.last_name.like("%{}%".format(search_query)),
                    models.ScheduleOrder.email.like("%{}%".format(search_query)),
                    models.ScheduleOrder.code.like("%{}%".format(search_query)),
                    models.ScheduleOrder.phone.like("%{}%".format(search_query)),
                    )
                )

    orders = create_admin_list(
        query,
        page,
        request.args,
        per_page=100
    )

    order_count = filtered_query_count(query, args=request.args, filters=[])

    return render_template("/admin/order_list.html", pagination=orders, searched_field=search_query, order_count=order_count)


@csrf.exempt
@blueprint.route("/order/delete", methods=["POST"])
@permission_required("schedule")
def order_delete():
    if not active_user().can_update("schedule"):
        abort(403)

    ids_to_delete = request.form.getlist("ids")
    db.session.begin(subtransactions=True)
    for id in ids_to_delete:
        obj = db.session.query(models.ScheduleOrder).get(id)
        if obj:
            obj.active = False
        db.session.add(obj)
    db.session.commit()
    return redirect(url_for(".order_list"))


@blueprint.route("/order/new", methods=["GET", "POST"])
@blueprint.route("/order/<int:id>", methods=["GET", "POST"])
@permission_required("schedule")
def order(id=None):
    if not active_user().can_update("schedule"):
        abort(403)

    if id:
        order = models.ScheduleOrder.query.get_or_404(id)
        order.guest_count = len(order.guests)
    else:
        order = models.ScheduleOrder()

    if 'delete' in request.form:
        db.session.begin(subtransactions=True)
        order.active = False
        db.session.add(order)
        db.session.commit()
        return redirect(url_for(".order_list"))

    schedule_id = request.args.get("schedule_id")
    if schedule_id is not None:
        schedule = models.Schedule.query.get_or_404(schedule_id)
        schedules = [schedule]
    else:
        schedules = models.Schedule.query\
                    .filter(models.Schedule.date >= date.today(),
                            models.Schedule.deleted is not True,)\
                    .order_by(models.Schedule.date).all()
        if order.schedule_id and order.schedule_id not in [x.id for x in schedules]:
            schedules = [order.schedule] + schedules

    email_form = forms.BulkEmailForm()
    conf_email = db.session.query(models.StaticPage)\
        .filter_by(path="/email/order-confirmation")\
        .one()
    email_form.subject.data = conf_email.title
    email_form.emails.data = order.email
    email_form.body.data = conf_email.body
    if order.schedule:
        email_form.from_email.data = order.schedule.campus.email

    form = forms.ScheduleOrderForm(request.form, obj=order)
    if form.validate_on_submit() and active_user().can_update("schedule"):
        db.session.begin(subtransactions=True)
        form.populate_obj(order)

        if order.cancelled and not order.datetime_cancelled:
            order.datetime_cancelled = datetime.now()

        posted_schedule = request.form.get("schedule", None)
        if posted_schedule:
            order.schedule_id = int(posted_schedule)

        guest_ids = request.form.getlist("guest_ids")
        guest_names = request.form.getlist("guest_names")
        guest_emails = request.form.getlist("guest_emails")
        guest_cancellations = request.form.getlist("guest_cancellations")
        guests = []
        for id, name, email, cancellation in izip_longest(guest_ids, guest_names, guest_emails, guest_cancellations):

            if id == "NEW":
                cancelled = True if cancellation else False
                guests.append(models.GuestOrder(name=name, email=email, cancelled=cancelled))
            else:
                guest = models.GuestOrder.query.get(id)
                guest.name = name
                guest.email = email
                guest.cancelled = id in guest_cancellations
                guests.append(guest)
        order.guests = guests
        db.session.add(order)
        db.session.commit()
        if "submit-continue" in request.form:
            return redirect(url_for(".order", id=order.id))
        return redirect(url_for(".order_list"))

    return render_template("/admin/order_edit.html",
                           form=form,
                           order=order,
                           schedules=schedules,
                           email_form=email_form)


@csrf.exempt
@blueprint.route("/order/<int:id>/confirm", methods=["POST"])
@permission_required("schedule")
def send_order_confirmation(id):
    order = models.ScheduleOrder.query.get_or_404(id)

    form = forms.BulkEmailForm()

    body = render_template_string(form.body.data, order=order)
    subject = render_template_string(form.subject.data, order=order)

    additional_emails = form.emails.data.split(',')
    all_emails = order.active_emails + filter(None, additional_emails)
    sender = order.schedule.campus.email

    message = site_emails.bulk_email(body, subject, None, email_list=all_emails, sender=sender)
    mail.send(message)
    return ""


@csrf.exempt
@blueprint.route("/gift-certificates/<int:id>/email", methods=["POST"])
@permission_required("schedule")
def send_gift_certificate_conf_email(id):
    cert = models.GiftCertificate.query.get_or_404(id)
    form = forms.GiftCertificateEmailForm()
    message = site_emails.gift_certificate_confirmation(cert, form)
    mail.send(message)
    return ""


@csrf.exempt
@blueprint.route("/content/images/new", methods=["POST"])
@permission_required("content")
def upload_images():
    if not active_user().can_update("content"):
        abort(403)

    image = request.files["upload"]
    base_name = os.path.basename(image.filename)
    image = utils.file_upload(image, base_name, 'content_images')
    utils.create_thumbnail(utils.path_on_disk('content_images', image), image)
    funcnum = request.args.get("CKEditorFuncNum")
    url = utils.url_path("content_images", image)
    message = ""
    return render_template("/admin/image_upload_results.html",
            funcnum=funcnum, url=url, message=url)

@csrf.exempt
@blueprint.route("/content/images")
@permission_required("content")
def browse_images():
    funcnum = request.args.get("CKEditorFuncNum")
    images = []
    for el in os.listdir(utils.path_on_disk("content_images")):
        images.append({
                "url": utils.url_path("content_images", el),
                "thumburl": utils.url_path("thumbnails", el),
                "filename": el,
            }
        )
    return render_template("/admin/image_browse.html",
                images=images,
                funcnum=funcnum
            )


@blueprint.route("/sales")
@blueprint.route("/sales/<int:page>")
def sales_list(page=1):
    search_query = request.args.get("q", "")
    campus_ids = session.get("campus_ids", [])

    selling_users = db.session.query(models.User)\
                        .select_from(models.ProductOrder)\
                        .join(models.Teacher)\
                        .join(models.User)\
                        .distinct().all()

    query = db.session.query(models.ProductOrder)\
        .outerjoin(models.Teacher, models.User, models.Purchase)\
        .order_by(models.ProductOrder.date_ordered.desc())\
        .filter(models.ProductOrder.campus_id.in_(campus_ids))\
        .distinct()

    if search_query:
        query = query.filter(or_(
                models.Product.name.like("%{}%".format(search_query)),
                models.Purchase.first_name.like("%{}%".format(search_query)),
                models.Purchase.last_name.like("%{}%".format(search_query)),
                models.Purchase.email.like("%{}%".format(search_query)),
                models.User.first_name.like("%{}%".format(search_query)),
                models.User.last_name.like("%{}%".format(search_query)),
            )
        )

    def sales_filters(query, args):
        if args.get("paid_with", None):
            query = query.filter(models.ProductOrder.paid_with == args.get("paid_with", ""))
        if args.get("sold_by", None):
            query = query.filter(models.ProductOrder.sold_by_id == args.get("sold_by", ""))

        return query

    orders = create_admin_list(
        query,
        page,
        request.args,
        filters=[sales_filters],
        sorters=sorting.sales_criteria,
        default_column='created',
        default_order='desc',
        per_page=100
    )

    return render_template(
        "/admin/sales_list.html",
        pagination=orders,
        searched_field=search_query,
        selected_paid_with=request.args.get("paid_with", None),
        selected_sold_by=request.args.get("sold_by", None),
        selling_users=selling_users,
        paid_with_choices=models.ProductOrder.PAID_WITH_CHOICES,
    )


@blueprint.route("/sales/edit/<int:id>", methods=["GET", "POST"])
@permission_required("sales_edit")
def sales_edit(id):
    order = models.ProductOrder.query.get_or_404(id)
    campus_ids = session.get("campus_ids", ())
    form = forms.ShopOrderForm.new(campus_ids, request.form, obj=order, user=active_user())
    if request.form.get("delete"):
        db.session.delete(order)
        db.session.flush()
        return redirect(url_for(".sales_list"))

    if form.validate_on_submit():
        db.session.begin(subtransactions=True)

        form.populate_obj(order)
        db.session.add(order)

        item_ids = request.form.getlist('item_id')
        item_ids = [int(x) if x.isdigit() else x for x in item_ids]
        products = request.form.getlist('product')
        qtys = [int(x) for x in request.form.getlist('item_qty')]
        amounts = request.form.getlist('item_total')
        shipping = request.form.getlist('item_shipping')
        tax = request.form.getlist('item_tax')

        for item in order.items:
            if item.id not in item_ids:
                order.remove_items([item])

        for item_id, product, qty, amt, shipping, tax in izip_longest(item_ids, products, qtys, amounts, shipping, tax):
            if item_id:  # item already on order
                item = next((x for x in order.items if x.id == item_id))
                item.quantity = qty
                item.discounted_subtotal = amt
                item.shipping = shipping
                item.tax = tax
                db.session.merge(item)
            else:
                product = db.session.query(models.Product).get(product)
                order.assign_products(order.campus, [(product, qty)], False)

        db.session.commit()

        if request.form.get("continue"):
            return redirect(url_for(".sales_edit", id=order.id))
        return redirect(url_for(".sales_list"))

    studio_products = db.session.query(models.Product, models.ProductInventory)\
                        .join(models.ProductInventory)\
                        .filter(models.ProductInventory.campus_id == order.campus_id)\
                        .filter(models.ProductInventory.quantity_stocked > 0)\
                        .all()

    return render_template("/admin/sales_edit.html",
                           form=form,
                           order=order,
                           studio_products=studio_products)
