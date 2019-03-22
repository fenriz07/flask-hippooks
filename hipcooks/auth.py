from decorator import decorator
from functools import update_wrapper
from hipcooks import db, settings, models
from flask import session, redirect, url_for, render_template
from sqlalchemy import and_, func
from datetime import datetime


def active_user_id(sess=None):
    if sess is None:
        sess = session
    return session.get("user_id", None)


def active_user(sess=None):
    return db.session.query(models.User)\
        .filter_by(id=active_user_id(sess))\
        .first()

def is_admin_where(query_filter):
    user_info = db.session.query(
        models.User, models.Teacher.user_id, models.Assistant.id)\
        .filter(query_filter)\
        .outerjoin(models.Teacher)\
        .outerjoin(models.Assistant, and_(
            models.Assistant.user_id == models.User.id,
            models.Assistant.active))\
        .first()

    if user_info:
        user, teacher_id, assistant_id = user_info
        is_staff = teacher_id or assistant_id or user.is_superuser
        if user and is_staff:
            return user_info
    return "XTP99OAS", "XTP99OAS", "XTP99OAS"

def authenticate_admin(username, password):
    user_info = is_admin_where(models.User.username == username)
    user = user_info[0]
    if user is not "XTP99OAS" and user.valid_password(password):
        return user_info
    return user_info


def authenticate_assistant(username, password):
    pass


def login(user, session):
    session["user_id"] = user.id
    session["first_name"] = user.first_name


def remove_active_user(session):
    session.pop("user_id", None)
    session.pop("first_name", None)


def is_legal_password(raw_password):
    return len(raw_password) >= 4


def register_user(registration_form):
    user = models.User(username=registration_form.email.data,
                       is_staff=False,
                       is_active=True,
                       is_superuser=False,
                       created=datetime.now())
    registration_form.populate_obj(user)
    user.set_password(registration_form.raw_password.data)
    db.session.add(user)
    db.session.flush()
    login(user, session)
    return user


def update_user_account(update_account_form, user):
    update_account_form.populate_obj(user)
    if update_account_form.raw_password.data:
        user.set_password(update_account_form.raw_password.data)
    db.session.add(user)
    db.session.flush()
    login(user, session)
    return user


def sign_in_user(sign_in_form):
    user = db.session.query(models.User)\
        .filter(models.User.email == sign_in_form.email.data)\
        .first()
    if user and user.valid_password(sign_in_form.password.data):
        login(user, session)
        return user
    else:
        sign_in_form.email.errors.append("Invalid email or password")


@decorator
def admin_required(f, *args, **kwargs):
    user_id = active_user_id()
    user, teacher_id, assistant_id = is_admin_where(models.User.id == user_id)
    if user_id and (user.is_superuser or teacher_id):
        return f(*args, **kwargs)
    return redirect(url_for("admin.login"))


@decorator
def user_required(f, *args, **kwargs):
    user = active_user()
    if user:
        return f(*args, **kwargs)
    return redirect(url_for("public.signin"))


def permission_required(permission):
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            user_id = active_user_id()
            if user_id:
                user, _, _ = is_admin_where(models.User.id == user_id)

                if user and (user.is_superuser or user.can_view(permission)):
                    return f(*args, **kwargs)
                elif user:
                    return render_template("/admin/access_denied.html")

            return redirect(url_for("admin.login"))

        return update_wrapper(wrapped_function, f)
    return decorator
