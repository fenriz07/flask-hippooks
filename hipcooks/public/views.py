from flask import (Blueprint, request, session, redirect, jsonify,
                   render_template, url_for, abort, make_response, Markup, flash)
from hipcooks import models, db, csrf, settings, utils, email, mail, auth
from hipcooks.auth import (user_required, sign_in_user, register_user,
                           update_user_account, active_user, active_user_id)
from hipcooks.cart import ShoppingCart
from hipcooks.public import forms, payment
import logging
from base64 import b32encode
from os import urandom
from datetime import datetime, date, time, timedelta
from sqlalchemy import func, or_
from authorize import AuthorizeError
from sqlalchemy.orm.exc import NoResultFound
import re
import json
from pytz import timezone
from hipcooks.auth import (
    login, permission_required)

logger = logging.getLogger("public")
blueprint = Blueprint("public", __name__, url_prefix="")


def active_studio(sess=None):
    if sess is None:
        sess = session
    session_studio_id = sess.get("studio_id")
    if session_studio_id is not None:
        return db.session.query(models.Campus).get(session_studio_id)

    domain_studio = db.session.query(models.Campus)\
                       .filter_by(domain=request.host)\
                       .first()
    if domain_studio is not None:
        sess["studio_id"] = domain_studio.id
        return domain_studio

    studio = db.session.query(models.Campus).first()
    sess["studio_id"] = studio.id
    return studio


def expire_cart_and_redirect(cart):
    cart_expired = cart.expire_on_timeout()
    if cart_expired:
        flash("We're sorry, but you've timed out! You will be automatically redirected to the Store page in five seconds.")
        if request.path.split('/')[-1] != 'cart':
            return redirect(url_for('public.cart') + '?timedOut=True')


@blueprint.context_processor
def inject_campus_info(sess=None):
    if sess is None:
        sess = session
    campuses = models.Campus.ordered_query().all()
    campus = active_studio()
    return {"campuses": campuses, "campus": campus,
            "cart": ShoppingCart(sess, campus)}


@blueprint.context_processor
def inject_today():
    return {"today": date.today()}


@blueprint.route("/", methods=["GET", ])
def index():
    return render_template("/public/index.html")


@blueprint.route("/policies")
def policies():
    return render_template("/public/policies.html")


@blueprint.route("/were-hiring")
def hiring():
    return render_template("/public/hiring.html")


@blueprint.route("/recipe_template", methods=["GET", ])
def recipe_template():
    return render_template("/public/recipe_template.html")

MONIKA_ID = 1


@blueprint.route("/about/hipcooks")
def about_hipcooks():
    return render_template("/public/about_hipcooks.html",
                           category="about-hipcooks", subnav="about")


@blueprint.route("/about/monika")
def about_monika():
    monika = db.session.query(models.Teacher).get(MONIKA_ID)
    return render_template("/public/about_monika.html", monika=monika,
                           category="about-monika", subnav="about")


@blueprint.route("/about/teachers")
def about_teachers():
    teachers = db.session.query(models.Teacher)\
        .join(models.TeacherCampus, models.Campus, models.User)\
        .filter(
            models.Campus.id == active_studio().id,
            models.Teacher.user_id != MONIKA_ID,
            models.User.is_active == True,
            models.Teacher.pic != None,
        )\
        .order_by(models.User.first_name)

    return render_template("/public/about_teachers.html", teachers=teachers,
                           category="about-teachers", subnav="about")


@blueprint.route("/resources", methods=["GET", ])
@blueprint.route("/resources/kitchen", methods=["GET", ])
def resources_kitchen():
    items = db.session.query(models.ResourcesKitchen)\
        .order_by(models.ResourcesKitchen.order.asc())
    large_appliances = items.filter_by(
        category=models.ResourcesKitchen.CATEGORY_LARGE_APPLIANCES)
    small_appliances = items.filter_by(
        category=models.ResourcesKitchen.CATEGORY_SMALL_APPLIANCES)
    kitchen_items = db.session.query(models.Product)\
        .order_by(models.Product.kitchen_row.asc(), models.Product.kitchen_column.asc())\
        .filter_by(is_resource=True)
    return render_template("/public/resources_kitchen.html",
                           large_appliances=large_appliances,
                           small_appliances=small_appliances,
                           kitchen_items=kitchen_items,
                           special_manufacturers=models.ResourcesKitchen.SPECIAL_MANUFACTURERS,
                           category="resources-kitchen", subnav="resources")


@blueprint.route("/resources/ingredients", methods=["GET", ])
def resources_ingredients():
    items = db.session.query(models.ResourcesIngredients)\
        .order_by(models.ResourcesIngredients.order.asc())
    search = request.args.get("q")
    if search is not None:
        search_param = "%{}%".format(search)
        items = items.filter(or_(
            models.ResourcesIngredients.name.like(search_param),
            models.ResourcesIngredients.description.like(search_param),
        ))
    return render_template("/public/resources_ingredients.html", items=items,
                           category="resources-ingredients",
                           subnav="resources")


@blueprint.route("/resources/markets", methods=["GET", ])
def resources_markets():
    markets = db.session.query(models.ResourcesMarket)\
        .filter_by(campus=active_studio())
    return render_template("/public/resources_markets.html", markets=markets,
                           form=forms.MarketFilterForm(),
                           category="resources-markets", subnav="resources")


@blueprint.route("/media", methods=["GET", ])
def media_landing():
    return render_template("/public/media_landing.html",
                           category="media", subnav="media")


@blueprint.route("/media/photos", methods=["GET", ])
def media_photos():
    studio_photos = db.session.query(models.ClassPhoto)\
                        .select_from(models.PhotoAlbum)\
                        .join(models.ClassPhoto)\
                        .join(models.Campus)\
                        .filter(models.PhotoAlbum.active == True)\
                        .order_by(
                                models.Campus.id != active_studio().id,
                                models.Campus.order,
                                models.ClassPhoto.order
                        ).all()
    additional_albums = models.PhotoAlbum.query.filter(
                            models.PhotoAlbum.active == True,
                            models.PhotoAlbum.campus == None
                        )\
                        .order_by(models.PhotoAlbum.name)\
                        .all()

    return render_template("/public/media_photos.html",
                        studio_photos=studio_photos,
                        additional_albums=additional_albums,
                        category="media-photos",
                        subnav="media"
            )


@blueprint.route("/media/about/mission", methods=["GET", ])
def media_mission():
    return render_template("/public/media_mission.html",
                           category="media-about-mission", subnav="media")


@blueprint.route("/media/about/monika", methods=["GET", ])
def media_monika():
    return render_template("/public/media_monika.html",
                           category="media-about-monika", subnav="media")


@blueprint.route("/media/about/hipcooks", methods=["GET", ])
def media_hipcooks():
    return render_template("/public/media_hipcooks.html",
                           category="media-about-hipcooks", subnav="media")


@blueprint.route("/media/video", methods=["GET", ])
def media_video():
    return render_template("/public/media_video.html",
                           category="media-video", subnav="media")


@blueprint.route("/media/testimonials", methods=["GET", ])
def media_testimonials():
    return render_template("/public/media_testimonials.html",
                           category="media-testimonials", subnav="media")


@blueprint.route("/media/press_login", methods=["GET", "POST"])
def media_press_login():
    contact_form = forms.ContactForm(request.form)
    sign_in_form = forms.SignInForm(request.form)
    if (sign_in_form.validate_on_submit()
        and "sign-in-submit" in request.sign_in_form):
            user = sign_in_user(sign_in_form)
            if user:
                return redirect(url_for(".media_press"))
    elif (contact_form.validate_on_submit() and "send-email" in request.contact_form):
        #mail.send(email.contact(contact_form.data, active_studio()))
        mail.send(email.contact(contact_form.data, "Darin@Molnar.com"))
    return render_template("/public/media_press_login.html", subnav="media", contact_form=contact_form, sign_in_form=sign_in_form)


@blueprint.route("/media/press", methods=["GET", ])
@permission_required('press')
def media_press():
    return render_template("/public/media_press.html",
                           category="media-press", subnav="media")


@blueprint.route("/campus/<id>")
def campus(id):
    session["studio_id"] = id
    return redirect(url_for('.class_landing'))


@blueprint.route("/signin", methods=["GET", "POST"])
def signin():
    sign_in_form = forms.SignInForm(request.form, prefix="sign-in")
    register_form = forms.RegisterForm(request.form, prefix="register")
    if ("sign-in-submit" in request.form and
            sign_in_form.validate_on_submit()):
        user = sign_in_user(sign_in_form)
        if user:
            return redirect(url_for(".dashboard"))
    elif ("register-submit" in request.form and
            register_form.validate_on_submit()):
            registered = register_user(register_form)
            models.Subscriber.create_subscriber(registered.username,
                                                registered.first_name + ' ' + registered.last_name,
                                                active_studio().id,
                                                'created_login')
            if registered:
                return redirect(url_for(".dashboard"))
    return render_template("/public/sign_in.html", sign_in_form=sign_in_form,
                           register_form=register_form, subnav="dashboard")


@blueprint.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = forms.ForgotPasswordForm()
    if form.validate_on_submit():
        db.session.begin()
        email_user = db.session.query(models.User)\
            .filter_by(email=form.email.data)\
            .first()
        if email_user is not None:
            link = models.ForgotPasswordLinks.new(email_user)
            db.session.add(link)
            link_url = url_for(".reset_password",
                               code=link.code, _external=True)
            message = email.email_forgot_password(email_user, link_url)
        else:
            message = email.email_forgot_password_invalid(form.email.data)
        mail.send(message)
        db.session.commit()
        return redirect(url_for(".forgot_password_confirm"))
    return render_template("/public/forgot_password.html", form=form)


@blueprint.route("/forgot-password-confirm")
def forgot_password_confirm():
    return render_template("/public/forgot_password_confirm.html")


@blueprint.route("/reset-password/<code>", methods=["GET", "POST"])
def reset_password(code):
    try:
        code = db.session.query(models.ForgotPasswordLinks)\
            .filter(
                models.ForgotPasswordLinks.code == code.lower(),
                models.ForgotPasswordLinks.expires >= datetime.now(),
                models.ForgotPasswordLinks.used == False,
            )\
            .one()
    except NoResultFound:
        abort(404)
    form = forms.ForgotPasswordResetForm()
    if form.validate_on_submit():
        db.session.begin()
        code.user.set_password(form.raw_password.data)
        db.session.merge(code.user)
        code.used = True
        db.session.merge(code)
        db.session.commit()
        auth.login(code.user, session)
        return redirect("/reset-password-complete")
    return render_template("/public/reset_password.html", form=form)


@blueprint.route("/reset-password-complete")
def reset_password_complete():
    return render_template("/public/reset_password_complete.html")

@blueprint.route("/logout", methods=["GET"])
def logout():
    auth.remove_active_user(session)
    ShoppingCart.empty_all(session)
    return redirect(url_for(".signin"))

@blueprint.route("/my-hipcooks", methods=["GET"])
@user_required
def dashboard():
    user = active_user()
    order_query = db.session.query(models.ScheduleOrder)\
        .join(models.Schedule)\
        .filter(models.ScheduleOrder.user_id == user.id)\
        .filter(models.ScheduleOrder.purchase != None)
    past_orders = [x for x in order_query if x.in_past]
    past_orders.sort(key=lambda x: x.schedule.date, reverse=True)
    future_orders = [x for x in order_query if not x.in_past]
    future_orders.sort(key=lambda x: x.schedule.date)

    gift_certs = models.GiftCertificate.outstanding_certs(user.email)
    return render_template("/public/dashboard.html",
                           user=user, past_orders=past_orders, future_orders=future_orders,
                           gift_certs_amounts=gift_certs, subnav="dashboard")


@blueprint.route("/my-notes", methods=["POST"])
@user_required
def mynotes():
    if "notes" in request.form:
        user = active_user()
        notes = db.session.query(models.UserNotes)\
                  .filter_by(user=user)\
                  .first()
        if notes is None:
            notes = models.UserNotes(user=user)
        notes.notes = request.form["notes"]
        db.session.begin(subtransactions=True)
        db.session.add(notes)
        db.session.commit()
    return request.form.get("notes", "")


@blueprint.route("/cancel-class/<order_code>", methods=["GET", "POST"])
@blueprint.route("/cancel-class/",  methods=["GET", "POST"])
def cancel_class(order_code = None):
    try:
        order, schedule, campus, cls = db.session.query(
                models.ScheduleOrder,
                models.Schedule,
                models.Campus,
                models.Class
            )\
            .filter(models.ScheduleOrder.code == order_code)\
            .join(models.Schedule, models.Campus, models.Class)\
            .one()
    except NoResultFound:
        abort(404)

    if order.in_past:
        abort(404)
    if order.past_cancellation_period:
        return redirect(url_for(".class_cancel_post_cancellation_period", schedule_order_id=order.id))
    if order.paid_with == 'GC' and 'refund-submit' in request.form:
        abort(400)
    if schedule.deleted:
        flash("This class has been canceled.")
        return redirect(url_for(".class_landing"))

    if request.method == "POST":
        schedule_was_full = not schedule.floored_remaining_spaces()
        order_cancelled = request.form.get("order_cancel")
        guests_cancelled = request.form.getlist("guest_cancel")
        db.session.begin(subtransactions=True)
        slots_cancelled = 0
        if order_cancelled is not None:
            changed_order = db.session.query(models.ScheduleOrder)\
                .get(order_cancelled)
            if not changed_order.cancelled:
                changed_order.cancelled = True
                changed_order.datetime_cancelled = datetime.utcnow()
                slots_cancelled += 1
            db.session.merge(changed_order)
        for guest_id in guests_cancelled:
            changed_guest = db.session.query(models.GuestOrder).get(guest_id)
            if not changed_guest.cancelled:
                changed_guest.cancelled = True
                slots_cancelled += 1
            db.session.merge(changed_guest)

        if slots_cancelled == 0:
            raise Exception("No slots specified to cancel. This should get caught by the front end.")

       # Send emails
        cancellation_notification_message = email.notify_studio_of_cancellation(schedule, order, slots_cancelled)
        mail.send(cancellation_notification_message)

        recipe_set = db.session.query(models.RecipeSet)\
                .filter(models.RecipeSet.id == cls.id)\
                .first()

        if recipe_set:
                recipe_message = email.send_recipes(schedule, order, recipe_set)
                mail.send(recipe_message)

        if schedule_was_full:
            waitlist_emails = [x.email for x in schedule.waitlists]
            message = email.schedule_spots_available_notice(schedule, waitlist_emails)
            mail.send(message)

        if "reschedule-submit" in request.form:
            cert = models.GiftCertificate(
                campus=models.Campus,
                created=datetime.utcnow(),
                sender_name=models.GiftCertificate.CATEGORY_MAKEUP,
                sender_email="hipcooks@hipcooks.com",
                amount_to_give=order.unit_price * slots_cancelled,
                recipient_name=order.first_name,
                recipient_email=order.email,
                message=models.GiftCertificate.CATEGORY_MAKEUP,
                giftcard=False,
                code=b32encode(urandom(5))[:7]
            )
            cert.campus = campus
            db.session.add(cert)
            db.session.commit()
            return redirect(url_for(".reschedule_endpoint", id=cert.id))
        elif 'refund-submit' in request.form:
            if order.paid_with == 'CC':
                payment.refund(order, slots_cancelled)
                message = email.refund(order)
                mail.send(message)
                db.session.commit()
                return redirect(url_for(".refund_endpoint"))
            elif order.paid_with == 'CC + GC':
                gc_amount_paid = order.gift_certificate_paid
                cc_amount_paid = order.paid - float(gc_amount_paid)

                cert = models.GiftCertificate(
                    campus=models.Campus,
                    created=datetime.now(),
                    sender_name=models.GiftCertificate.CATEGORY_MAKEUP,
                    sender_email="hipcooks@hipcooks.com",
                    amount_to_give=gc_amount_paid,
                    recipient_name=order.first_name,
                    recipient_email=order.email,
                    message=models.GiftCertificate.CATEGORY_MAKEUP,
                    giftcard=False,
                    code=b32encode(urandom(5))[:7]
                )
                cert.campus = campus
                db.session.add(cert)

                payment.refund(order, slots_cancelled, cc_amount_paid=cc_amount_paid)
                message = email.refund(order)
                mail.send(message)
                db.session.commit()

            return redirect(url_for(".reschedule_and_refund_endpoint", id=cert.id))

    show_refund_option = order.paid_with in ('CC', 'CC + GC')
    return render_template("/public/cancel_class.html", order=order,
                           schedule=schedule, campus=campus, cls=cls,
                           guests=order.guests, category="class-cancel",
                           subnav="class", show_refund_option=show_refund_option)

@blueprint.route("/class-cancel-post-cancellation-period/<schedule_order_id>", methods=['GET', 'POST'])
def class_cancel_post_cancellation_period(schedule_order_id):
    try:
        order, schedule, campus, cls = db.session.query(
                models.ScheduleOrder,
                models.Schedule,
                models.Campus,
                models.Class
            )\
            .filter(models.ScheduleOrder.id == schedule_order_id)\
            .join(models.Schedule, models.Campus, models.Class)\
            .one()
    except NoResultFound:
        abort(404)

    if request.method == "POST":
        if 'go-back' in request.form:
            return redirect(url_for(".dashboard"))
        elif 'cancel-submit' in request.form:
            schedule_was_full = not schedule.floored_remaining_spaces()

            order_cancelled = request.form.get("order_cancel")
            guests_cancelled = request.form.getlist("guest_cancel")
            db.session.begin(subtransactions=True)
            slots_cancelled = 0
            if order_cancelled is not None:
                changed_order = db.session.query(models.ScheduleOrder)\
                    .get(order_cancelled)
                if not changed_order.cancelled:
                    changed_order.cancelled = True
                    changed_order.datetime_cancelled = datetime.now()
                    slots_cancelled += 1
                db.session.merge(changed_order)
            for guest_id in guests_cancelled:
                changed_guest = db.session.query(models.GuestOrder).get(guest_id)
                if not changed_guest.cancelled:
                    changed_guest.cancelled = True
                    slots_cancelled += 1
                db.session.merge(changed_guest)

            if slots_cancelled == 0:
                raise Exception("No slots specified to cancel. This should get caught by the front end")

            # Send emails
            cancellation_notification_message = email.notify_studio_of_cancellation(schedule, order, slots_cancelled)
            mail.send(cancellation_notification_message)

            recipe_set = db.session.query(models.RecipeSet)\
                                   .filter(models.RecipeSet.id == cls.id)\
                                   .first()
            if recipe_set:
                recipe_message = email.send_recipes(schedule, order, recipe_set)
                mail.send(recipe_message)

            if schedule_was_full and schedule.floored_remaining_spaces():
                waitlist_emails = [x.email for x in schedule.waitlists]
                message = email.schedule_spots_available_notice(schedule, waitlist_emails)
                mail.send(message)

            return redirect(url_for(".class_cancel_post_cancellation_period_endpoint"))

    return render_template("/public/class_cancel_post_cancellation_period.html",
                           order=order, schedule=schedule, campus=campus, cls=cls,
                           category="class-cancel", subnav="class")


@blueprint.route("/cancel-reschedule-completed/<id>")
def reschedule_endpoint(id):
    cert = db.session.query(models.GiftCertificate).get(id)
    return render_template("/public/reschedule_endpoint.html", code=cert.code,
                           category="class-cancel", subnav="class")


@blueprint.route("/cancel-refund-completed")
def refund_endpoint():
    return render_template("/public/refund_endpoint.html",
                           category="class-cancel", subnav="class")


@blueprint.route("/cancel-reschedule-and-completed/<id>")
def reschedule_and_refund_endpoint(id):
    cert = db.session.query(models.GiftCertificate).get(id)
    return render_template("/public/reschedule_and_refund_endpoint.html", code=cert.code,
                           category="class-cancel", subnav="class")


@blueprint.route("/class-cancel-post-cancellation-period-endpoint")
def class_cancel_post_cancellation_period_endpoint():
    return render_template("/public/class_cancel_post_cancellation_period_endpoint.html",
                           category="class-cancel", subnav="class")


@blueprint.route("/update-info", methods=["GET", "POST"])
@user_required
def update_info():
    user, newsletter = db.session.query(models.User, models.Subscriber)\
        .filter_by(id=active_user_id())\
        .outerjoin(models.Subscriber,
                   models.User.email == models.Subscriber.email)\
        .one()
    form = forms.UpdateAccountInfoForm.new(request.form, user, newsletter)
    if form.validate_on_submit(user):
        db.session.begin()
        update_user_account(form, user)
        if newsletter is None:
            newsletter = models.Subscriber()
        newsletter.change_email(form.email.data)
        newsletter.name = "{} {}".format(user.first_name, user.last_name)
        newsletter.campus = active_studio()
        newsletter.active = bool(form.subscriber.data)
        newsletter.subscribe_reason = 'created_login'
        db.session.add(newsletter)
        db.session.commit()
        return redirect(url_for(".dashboard"))
    return render_template("/public/update_info.html", form=form,
                           subnav="dashboard")


@blueprint.route("/subscribe_to_newsletter", methods=["POST"])
def subscribe_to_newsletter():
    form = request.form
    db.session.begin()
    newsletter = models.Subscriber()
    newsletter.name = form.get('newsletter_name')
    newsletter.email = form.get('newsletter_email')
    newsletter.subscribe_reason = 'newsletter_signup'
    newsletter.campus_id = active_studio().id
    db.session.add(newsletter)
    db.session.commit()
    return ''


@blueprint.route("/classes")
def class_landing():
    return render_template("/public/class_landing.html", subnav="class")


@blueprint.route("/classes/list")
def class_list(now=None):
    if now is None:
        now = date.today()
    scheduled_classes = db.session.query(models.Schedule)\
        .filter(models.Schedule.date >= now)\
        .filter(models.Schedule.campus == active_studio())\
        .filter(models.Schedule.deleted is not True)\
        .order_by(models.Schedule.date.asc())
    return render_template("/public/class_list.html",
                           scheduled_classes=scheduled_classes,
                           category="class-schedule", subnav="class")


@blueprint.route("/classes/details")
def class_descriptions():
    classes = db.session.query(models.Class)
    filter_select = request.args.get("filter_select", "")

    if filter_select:
        if filter_select == 'knife skills':
            classes = classes.order_by(models.Class.knife_level.asc(),models.Class.order.asc())
        elif filter_select == 'vegetarian':
            classes = classes.order_by(models.Class.veggie_level.asc(),models.Class.order.asc())
        elif filter_select == 'dairy-free':
            classes = classes.order_by(models.Class.dairy_level.asc(),models.Class.order.asc())
        elif filter_select == 'wheat-free':
            classes = classes.order_by(models.Class.wheat_level.asc(),models.Class.order.asc())

    return render_template("/public/class_descriptions.html", classes=classes,
                           category="class-descriptions", Class=models.Class,
                           filter_select=filter_select, subnav="class")


@blueprint.route("/classes/schedule/<schedule_id>", methods=["GET", "POST"])
def class_details(schedule_id):
    schedule, details = db.session.query(models.Schedule, models.Class)\
        .filter_by(id=schedule_id)\
        .join(models.Class)\
        .one()
    user = active_user()
    form = None
    register_form = forms.SchedulingRegisterForm(
        request.form, prefix="register", remaining_spaces=schedule.floored_remaining_spaces())
    sign_in_form = forms.SchedulingSignInForm(
        request.form, prefix="sign-in", remaining_spaces=schedule.floored_remaining_spaces())
    schedule_form = forms.ScheduleForm(request.form,
                                       remaining_spaces=schedule.floored_remaining_spaces())
    if register_form.validate_on_submit():
        user = register_user(register_form)
        form = register_form
        models.Subscriber.create_subscriber(form.email.data,
                                            form.first_name.data + ' ' + form.last_name.data,
                                            schedule.campus.id,
                                            'class_signup')
    elif sign_in_form.validate_on_submit():
        user = sign_in_user(sign_in_form)
        form = sign_in_form
    elif user and schedule_form.validate_on_submit():
        form = schedule_form

    guest_info = []
    if form:
        guest_name_fields = [x for x in request.form if 'guest_name_' in x]
        for name_field in guest_name_fields:
            guest_dict = {}
            guest_number = name_field.split('_')[-1]
            guest_dict['name'] = request.form[name_field]
            guest_dict['email'] = request.form['guest_email_' + str(guest_number)]
            guest_info.append(guest_dict)

    if form and schedule.floored_remaining_spaces() and form.guests.data <= schedule.floored_remaining_spaces():
        cart = ShoppingCart(session, active_studio())
        cart_expired = expire_cart_and_redirect(cart)
        if cart_expired:
            return cart_expired
        cart.add_class(
            schedule, form.guests.data, form.comments.data, json.dumps(guest_info))
        return redirect(url_for(".cart"))
    elif form:
        db.session.begin(subtransactions=True)
        db.session.add(
            models.WaitingList(schedule=schedule,
                               name=user.first_name,
                               email=user.email,
                               phone="",
                               guests=form.guests.data,
                               guest_information=json.dumps(guest_info)))
        db.session.commit()
        return redirect(url_for(".waitlist"))
    return render_template("/public/class_schedule.html", schedule=schedule,
                           details=details, sign_in_form=sign_in_form,
                           register_form=register_form,
                           schedule_form=schedule_form,
                           user_id=active_user_id(),
                           category="class-descriptions", subnav="class")


@blueprint.route("/classes/cancel", methods=["GET", "POST"])
def class_cancel_retrieve():
    form = forms.ReservationLookupForm()
    if form.validate_on_submit():
        return redirect(url_for(".cancel_class", order_code=form.code.data))
    return render_template("/public/class_cancel_retrieve.html", form=form,
                           category="class-cancel", subnav="class")


@blueprint.route("/classes/private", methods=["GET", "POST"])
def class_private():
    form = forms.PrivateClassRequestForm()
    if form.validate_on_submit():
        campus = active_studio()
        message = email.private_class(form.data, campus.name)
        mail.send(message)
        return redirect(url_for(".class_list"))
    return render_template("/public/private_classes.html", form=form,
                            category="class-private", subnav="class",
                            studio=active_studio())


@blueprint.route("/classes/gift", methods=["GET", "POST"])
def class_gift():
    gift_cert_form = forms.GiftCertificateForm()
    mailing_info_form = forms.GiftCertificateMailingInfoForm()
    if gift_cert_form.validate_with_mailing_info(mailing_info_form):
        cart = ShoppingCart(session, active_studio())
        cart_expired = expire_cart_and_redirect(cart)
        if cart_expired:
            return cart_expired
        cart.add_gift_certificate(request.form)
        return redirect(url_for(".cart") + '?itemAddedToCart=True')
    return render_template("/public/class_gift_certificate.html",
                           gift_cert_form=gift_cert_form,
                           mailing_info_form=mailing_info_form,
                           category="class-gift-cert", subnav="class")


@blueprint.route("/store")
def store():
    # The following breaks mobile layout in favor of a fixed table
    # that assumes the design will never change, by displaying products
    # in a grid defined by the user into a roughly desktop-sized format.
    # If products in a cell are missing, or are inactive in a particular
    # store, they will simply not appear -- there will be a hole. If two
    # products share the same cell, the first one wins.
    #
    # This is so Monika can have complete control of layout, and per Kyrsten,
    # she has accepted the potential consequences of this face-palmable design
    # decision. Let our successors (who presumably know about responsive design)
    # not judge us too harshly...

    max_row = db.session.query(func.max(models.Product.row))\
            .select_from(models.Product)\
            .join(models.ProductInventory)\
            .filter(
                models.ProductInventory.active == True,
                models.ProductInventory.campus == active_studio()
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
                models.ProductInventory.campus == active_studio()
            )\
            .order_by(models.Product.row, models.Product.column)

    for product in products:
        if grid[product.row - 1][product.column - 1] is None:
            grid[product.row - 1][product.column - 1] = product

    return render_template("/public/store_list.html",
                           product_grid=grid, subnav="store")


@blueprint.route("/store/cookbook", endpoint="shop_cookbook",
                 defaults={"product_id": 165}, methods=["GET", "POST"])
@blueprint.route("/store/product/<int:product_id>", methods=["GET", "POST"])
def store_product(product_id):
    product = db.session.query(models.Product).get(product_id)
    related_products = db.session.query(models.Product)\
        .filter(models.Product.name == product.name)
    if product is None:
        abort(404)
    studio = active_studio()
    stock = models.ProductInventory.stocked(studio.id, product_id)
    sold = models.ProductOrderItem.sold(studio.id, product_id)

    form = forms.StoreProductForm()
    if form.validate_with_quantity(stock):
        cart = ShoppingCart(session, studio)
        cart_expired = expire_cart_and_redirect(cart)
        if cart_expired:
            return cart_expired
        cart.add_product(product, form.quantity.data)
        return redirect(url_for(".cart") + '?itemAddedToCart=True')

    return render_template("/public/store_product.html", product=product,
                           remaining=stock, form=form,
                           related_products=related_products, subnav="store")


@blueprint.route("/store/product/details")
def store_product_details():
    product_id = request.args["id"]
    product = models.Product.query.get_or_404(product_id)
    return jsonify(
        type=product.type.title(),
        name=product.name,
        image_url=product.url,
        price=format(product.price, "0.2f"),
        description=product.description_or_default,
        quantity=product.remaining(active_studio().id),
    )


@blueprint.route("/cart")
def cart():
    cart = ShoppingCart(session, active_studio())
    cart_expired = expire_cart_and_redirect(cart)
    if cart_expired:
        return cart_expired
    if "store" in request.headers.get("REFERER", ""):
        continue_url = url_for(".store")
    else:
        continue_url = url_for(".class_list")

    return render_template("/public/cart.html", continue_url=continue_url,
                           subnav="store")


@blueprint.route("/cart/remove/schedule/<id>", methods=["POST"])
def cart_schedule_remove(id):
    cart = ShoppingCart(session, active_studio())
    cart.remove_class(id)
    return jsonify(cart.totals)


@blueprint.route("/cart/remove/gift_certificate/<id>", methods=["POST"])
def cart_gift_cert_remove(id):
    cart = ShoppingCart(session, active_studio())
    cart.remove_gift_certificate(id)
    return jsonify(cart.totals)


@blueprint.route("/cart/remove/product/<id>", methods=["POST"])
@blueprint.route("/cart/remove/product/", build_only=True)
def cart_product_remove(id):
    cart = ShoppingCart(session, active_studio())
    cart.remove_product(id)
    return jsonify(cart.totals)


@blueprint.route("/cart/update/products", methods=["POST"])
def cart_product_quantity_update():
    ids = map(int, request.form.getlist("product_id"))
    quantities = map(int, request.form.getlist("quantity"))
    cart = ShoppingCart(session, active_studio())
    cart.update_product_quantities(zip(ids, quantities))
    return jsonify(cart.totals)


@blueprint.route("/cart/update/pickup", methods=["POST"])
def cart_pickup_set():
    cart = ShoppingCart(session, active_studio())
    cart.pickup = True if request.form["pickup"] == "true" else False

    return jsonify(cart.totals)


@blueprint.route("/cart/product-info")
def cart_product_info(draw=0):
    cart = ShoppingCart(session, active_studio())
    products = cart.products

    return jsonify(
        draw=int(draw),
        recordsTotal=len(products),
        recordsFiltered=len(products),
        data=[{
                "product_id": p.id,
                "name": p.name,
                "price": format(p.price, ".2f"),
                "quantity": q,
                "shipping": format(p.shipping_price(q, cart.pickup), ".2f"),
                "total": format(p.base_price(q), ".2f"),
            } for p, q in products
        ],
    )


@blueprint.route("/cart/gift-certificate/", methods=["POST"])
def apply_gift_certificate():
    gift_code = request.form.get("gift_code")
    gift_certificate = db.session.query(models.GiftCertificate)\
        .filter_by(code=gift_code)\
        .scalar()
    cart = ShoppingCart(session, active_studio())
    cart.apply_gift_certificate(gift_certificate)
    return jsonify(cart.totals)


@blueprint.route("/classes/waitlist")
def waitlist():
    return render_template("/public/waitlist.html", category="class-schedule",
                           subnav="class")


# TODO: I'm not comfortable with this view being this big...should refactor
# into a separate module, maybe renaming payment to order and putting
# subroutines in there.
@blueprint.route("/checkout", methods=["GET", "POST"])
def checkout():
    user_id = active_user_id()
    campus = active_studio()
    user = active_user()

    cart = ShoppingCart(session, campus)
    cart_expired = expire_cart_and_redirect(cart)
    if cart_expired:
        return cart_expired

    if cart.products:
        if cart.pickup:
            form = forms.NonShippingCheckoutForm(request.form)
        else:
            form = forms.ShippingCheckoutForm(request.form)
    else:
        form = forms.NonShippingCheckoutForm(request.form)
    if not cart.payment_needed:
        form.remove_payment_form()

    if request.method == "POST":
        if form.validate():
            try:
                first_name, last_name = tuple(form.billing_address.data["name"].split(" ", 1))
            except ValueError:
                first_name = form.billing_address.data["name"]
                last_name = ""

            pf = payment.PaymentFinalizer(user_id, campus, cart)
            try:
                if cart.payment_needed:
                    pf.purchase(form.payment.data["cc_number"],
                                form.payment.data["cc_exp_year"],
                                form.payment.data["cc_exp_month"],
                                form.payment.data["cc_vv"],
                                first_name,
                                last_name)
                pf.record_purchase(request.environ["REMOTE_ADDR"],
                                   first_name,
                                   last_name,
                                   form.billing_address.data["address_line_1"],
                                   form.billing_address.data["address_line_2"],
                                   form.billing_address.data["city"],
                                   form.billing_address.data["state"],
                                   form.billing_address.data["zip_code"],
                                   form.email.data,
                                   form.phone.data)
                for gc in pf.purchased_gift_certificates:
                    message = email.gift_certificate(gc)
                    mail.send(message)
                for cls in pf.purchased_classes:
                    message = email.email_order_confirmation(cls)
                    mail.send(message)

                # Sign up the purchaser for the newsletter as appropriate
                if pf.purchased_classes:
                    models.Subscriber.create_subscriber(form.email.data, form.name.data, campus.id, 'class_signup')
                elif pf.purchased_gift_certificates:
                    models.Subscriber.create_subscriber(form.email.data, form.name.data, campus.id, 'bought_gc')

                cart.empty()
                return redirect(url_for(".dashboard") + '?orderCompleted=True')
            except AuthorizeError, e:
                #TODO: Make this user-friendly by regexping out the part the user should see.
                # For now we'll leave it like this for debugging purposes.
                form.payment.form.cc_number.errors.append(str(e))

    return render_template("/public/checkout.html",
                           form=form,
                           cart=cart,
                           subnav="store",
                           user=user)


@blueprint.route("/pages/<path:path>")
def pages(path):
    page = db.session.query(models.StaticPage)\
        .filter_by(path=path)\
        .scalar()
    if page is None:
        abort(404)
    return render_template("/public/generic.html", title=page.title,
                           body=Markup(page.body))


@blueprint.route("/recipes/<class_id>")
def recipes(class_id):
    recipe_set = models.RecipeSet.query.get_or_404(class_id)
    return render_template("/public/recipe.html", recipe_set=recipe_set,
                           class_id=class_id, subnav="dashboard")


@blueprint.route("/recipes/preview/<int:class_id>")
def recipes_preview(class_id):
    env = utils.nonHTMLJinjaEnv()
    try:
        cls, recipe_set = db.session.query(models.Class, models.RecipeSet)\
            .join(models.RecipeSet)\
            .filter(models.Class.id == class_id)\
            .one()
    except NoResultFound:
        abort(404)

    header_image = utils.base_64_encoded_file('static/img/printheadergraphic.png')

    return env.get_template("/recipe_preview.html").render(recipe_set=recipe_set,
                                                           cls=cls,
                                                           header_image=header_image,
                                                           print_on_load=True)


@blueprint.route("/directions")
def directions():
    return render_template("/public/directions.html", subnav="directions")


@blueprint.route("/contact", methods=["GET", "POST"])
def contact():
    form = forms.ContactForm()
    if form.validate_on_submit():
        models.Subscriber.create_subscriber(form.email.data, form.name.data, active_studio().id, 'contact_page_email')
        mail.send(email.contact(form.data, active_studio()))
        return redirect(url_for(".class_landing"))
    return render_template("/public/contact.html", form=form, subnav="contact")
