from flask import render_template_string, render_template, url_for
from flask.ext.mail import Message
from hipcooks import app, models, db, settings, utils

def private_class(private_class_form_data, studio):
    private_class_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/private-class-request")\
        .one()
    return Message(
        html=render_template_string(
            private_class_content.body,
            studio=studio,
            **private_class_form_data
        ),
        subject=render_template_string(
            private_class_content.title,
            studio=studio,
            **private_class_form_data
        ),
        sender=private_class_form_data["email"],
        recipients=[app.config["HIPCOOKS_REQUEST_EMAIL_ADDRESS"]]
    )


def gift_certificate(certificate):
    if certificate.is_card:
        return card_request(certificate)
    else:
        return email_gift_certificate(certificate)


def card_request(certificate):
    card_request_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/card-request")\
        .one()
    return Message(
        html=render_template_string(
            card_request_content.body, cert=certificate),
        subject=render_template_string(
            card_request_content.title, cert=certificate),
        sender=certificate.sender_email,
        recipients=[app.config["HIPCOOKS_REQUEST_EMAIL_ADDRESS"]],
    )


def email_gift_certificate(certificate):
    cert_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/gift-certificate")\
        .one()
    if certificate.is_for_recipient:
        recipients = [certificate.recipient_email]
        bcc = [certificate.sender_email]
    else:
        recipients = [certificate.sender_email]
        bcc = []
    return Message(
        html=render_template_string(cert_content.body, cert=certificate),
        subject=render_template_string(cert_content.title, cert=certificate),
        sender="noreply@hipcooks.com",
        recipients=recipients,
        bcc=bcc,
    )


def gift_certificate_confirmation(cert, form):
    email_type = form.email_type.data
    date_sent = form.date_sent.data
    body = render_template_string(form.body.data, cert=cert, date_sent=date_sent)
    subject = render_template_string(form.subject.data, cert=cert, date_sent=date_sent)
    recipient = form.recipient.data

    message = Message(
        html=body,
        subject=subject,
        sender=form.from_email.data,
        recipients=[recipient],
    )

    if email_type == 'pdf':
        message.attach('Hipcooks_Gift_Certificate.pdf', 'application/pdf', form.pdf.data.read())
    elif email_type == 'pdf_and_receipt':
        message.attach('Hipcooks_Gift_Certificate.pdf', 'application/pdf', form.pdf.data.read())
        message.attach('Hipcooks_Gift_Certificate_Receipt.pdf', 'application/pdf', form.receipt.data.read())

    return message


def refund(order):
    refund_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/refund")\
        .one()
    return Message(
        html=render_template_string(refund_content.body),
        subject=render_template_string(refund_content.title),
        sender="noreply@hipcooks.com",
        recipients=[order.email],
    )


def class_report(report):
    message = render_template("/admin/emails/class_report.html",
        report=report,
        sales_rating=models.ClassReport.SALES_CHOICES[str(report.sales_rating)],
        class_rating=models.ClassReport.CLASS_CHOICES[str(report.class_rating)],
        assistant_rating=models.ClassReport.ASSISTANT_CHOICES[str(report.assistant_rating)],
        pacing_rating=models.ClassReport.PACING_CHOICES[str(report.pacing_rating)],
        tasting_rating=models.ClassReport.TASTING_CHOICES[str(report.tasting_rating)],
        preprep_rating=models.ClassReport.PREPREP_CHOICES[str(report.preprep_rating)],
        breakage_rating=models.ClassReport.BREAKAGE_CHOICES[str(report.breakage_rating)],
        report_url = "http://{}{}".format(settings.URL, url_for(".schedule_report", id=report.id)),
    )
    message = "Teacher Class Report Test Message"
    return Message(
        html=message,
        subject="{}'s Class Report: {} on {} @ {}".format(
                                                    report.schedule.teachers[0],
                                                    report.schedule.cls.abbr,
                                                    report.schedule.date.strftime('%m/%d/%y'),
                                                    report.schedule.campus
                                                    ),
        sender=app.config["MAIL_SENDER"],
        recipients=[app.config["HIPCOOKS_REQUEST_EMAIL_ADDRESS"]])


def class_report_comment(report, comment, send_to):
    message = render_template("/admin/emails/class_report_comment.html",
                                report=report,
                                comment=comment,
                                report_url="http://{}{}".format(settings.URL, url_for(".schedule_report", id=report.id)),
                            )

    #TODO: Make this work for external emails. For now, since we're going to staging.
    recipients = []
    for staff_type in send_to:
        if staff_type == "teacher":
            recipients = recipients + [teacher.user.email for teacher in report.schedule.teachers]
        if staff_type == 'prep':
            recipients + recipients + [assistant.email for assistant in report.schedule.assistants]
        if staff_type == 'allteacher':
            recipients + recipients + [teacher.user.email for teacher in report.schedule.campus.teachers]
        if staff_type == 'manager':
            recipients = recipients + [report.schedule.campus.email]
        if staff_type == 'allmanager':
            recipients = recipients + [campus.email for campus in db.session.query(models.Campus).all()]
            monika = models.Teacher.get_monika()
            kyrsten = models.Teacher.get_kyrsten()
            recipients = recipients + [monika.user.email, kyrsten.user.email]

    recipients = list(set(recipients))

    if not recipients:
        recipients = recipients + [campus.email for campus in db.session.query(models.Campus).all()]
        monika = models.Teacher.get_monika()
        kyrsten = models.Teacher.get_kyrsten()
        recipients = recipients + [monika.user.email, kyrsten.user.email]

    recipients = filter(None, list(set(recipients)))

    return Message(
        html=message,
        subject="New Comment on {}'s Class Report: {} on {} @ {}".format(
                                                        report.schedule.teachers[0],
                                                        report.schedule.cls.abbr,
                                                        report.schedule.date.strftime('%m/%d/%y'),
                                                        report.schedule.campus
                                                    ),
        sender=app.config["HIPCOOKS_REQUEST_EMAIL_ADDRESS"],
        recipients=recipients)


def contact(contact_form_data, studio):
    contact_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/contact")\
        .one()
    return Message(
        html=render_template_string(
            contact_content.body, studio=studio, **contact_form_data),
        subject=render_template_string(
            contact_content.title, studio=studio, **contact_form_data),
        sender=contact_form_data["email"],
        recipients=[app.config["HIPCOOKS_CONTACT_EMAIL_ADDRESS"]])


def bulk_email(body, subject, email_results, email_list=None, sender=None):
    if not sender:
        sender = "noreply@hipcooks.com"
    if email_results:
        bcc = [email for (email,) in email_results]
    else:
        bcc = []
    if email_list:
        bcc += email_list
    return Message(
        html=body,
        subject=subject,
        sender=sender,
        bcc=bcc,
    )


def schedule_spots_available_notice(schedule, email_list):
    spots_available_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/spots-available")\
        .one()
    sender = schedule.campus.email or "noreply@hipcooks.com"
    return Message(
        html=render_template_string(spots_available_content.body, schedule=schedule),
        subject=render_template_string(spots_available_content.title, schedule=schedule),
        sender=sender,
        bcc=email_list,
    )


def notify_studio_of_cancellation(schedule, order, slots_cancelled):
    cancellation_notice_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/studio-cancellation-notice")\
        .one()
    return Message(
        html=render_template_string(cancellation_notice_content.body, schedule=schedule, order=order, slots_cancelled=slots_cancelled),
        subject=render_template_string(cancellation_notice_content.title, schedule=schedule),
        sender="noreply@hipcooks.com",
        recipients=[schedule.campus.email],
        #recipients=[settings.MAIL_USERNAME],
    )


def send_recipes(schedule, order, recipe_set):
    env = utils.nonHTMLJinjaEnv()
    header_image = utils.base_64_encoded_file('static/img/printheadergraphic.png')
    template = env.get_template("/recipe_preview.html").render(recipe_set=recipe_set,
                                                               cls=schedule.cls,
                                                               header_image=header_image)
    sender = schedule.campus.email or "noreply@hipcooks.com"
    return Message(
        html=template,
        subject="Hipcooks Class Recipes: {}".format(schedule.cls.title),
        sender=sender,
        recipients=[order.email],
    )


def assistant_email(assistant, campus, email_form):
    return Message(
        html=email_form.body.data,
        subject=email_form.subject.data,
        sender=assistant.email,
        recipients=[campus.email],
    )


def email_forgot_password(user, forgot_password_link):
    forgot_password_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/forgot-password")\
        .one()
    return Message(
        html=render_template_string(
            forgot_password_content.body, user=user,
            forgot_password_link=forgot_password_link),
        subject=render_template_string(
            forgot_password_content.title, user=user),
        sender="noreply@hipcooks.com",
        recipients=[user.email],
    )


def email_forgot_password_invalid(email):
    invalid_email_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/forgot-password-invalid")\
        .one()
    return Message(
        html=render_template_string(invalid_email_content.body, email=email),
        subject=render_template_string(
            invalid_email_content.title, email=email),
        sender="noreply@hipcooks.com",
        recipients=[email],
    )


def email_order_confirmation(order):
    conf_content = db.session.query(models.StaticPage)\
        .filter_by(path="/email/order-confirmation")\
        .one()

    return Message(
        html=render_template_string(conf_content.body, order=order),
        subject=render_template_string(conf_content.title, order=order),
        sender="noreply@hipcooks.com",
        recipients=[order.email],
    )


def bulk_email_recipe(recipe_form, template):
    recipients = re.split(r"(?:\s|,)+", recipe_form.to.data.strip())

    return [
        Message(
            html=template,
            subject=recipe_form.subject.data,
            sender=recipe_form.from_.data,
            recipients=[recipient],
        ) for recipient in recipients
    ]
