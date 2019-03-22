from itertools import chain, groupby
from hipcooks import db, models
from hipcooks.utils import csv_from_rows
from hipcooks.admin import forms
from operator import itemgetter
from sqlalchemy import and_, column, func, select, or_


def gift_certificate_report(studio, categories, start_date, end_date, period_label):
    filters = [models.GiftCertificate.created >= start_date,
               models.GiftCertificate.created <= end_date]
    if studio is not None:
        filters.append(models.Campus.id == studio.id)

    if len(categories) > 1:
        filters.append(models.GiftCertificate.paid_with.in_(categories))
    elif len(categories) == 1:
        filters.append(models.GiftCertificate.paid_with == categories[0])

    created_query = select((
        models.Campus.name,
        models.Campus.id,
        func.extract("YEAR", models.GiftCertificate.created).label("year"),
        func.sum(models.GiftCertificate.amount_to_give).label("created"),
    )).select_from(
        models.GiftCertificate.__table__
        .join(models.Campus)
    ).where(and_(*filters))\
        .group_by(models.GiftCertificate.campus_id, column("year"))\
        .alias("created")

    used_original_campus_query = select((
        models.Campus.name,
        models.Campus.id,
        func.extract("YEAR", models.GiftCertificateUse.date).label("year"),
        func.sum(models.GiftCertificateUse.amount).label("used"),
    )).select_from(
        models.GiftCertificateUse.__table__
        .join(models.GiftCertificate)
        .join(models.Campus,
              models.GiftCertificate.campus_id == models.Campus.id)
    ).where(and_(*filters))\
        .group_by(models.GiftCertificate.campus_id, column("year"))\
        .alias("used_original_campus")

    used_at_campus_query = select((
        models.Campus.name,
        models.Campus.id,
        func.extract("YEAR", models.GiftCertificateUse.date).label("year"),
        func.sum(models.GiftCertificateUse.amount).label("used"),
    )).select_from(
        models.GiftCertificateUse.__table__
        .join(models.GiftCertificate)
        .join(models.Campus,
              models.GiftCertificateUse.campus_id == models.Campus.id)
    ).where(and_(*filters))\
        .group_by(models.GiftCertificateUse.campus_id, column("year"))\
        .alias("used_at_campus")

    gift_certificate_query = select((
        created_query.c.name,
        created_query.c.campus_id,
        created_query.c.year,
        created_query.c.created,
        used_original_campus_query.c.used,
        used_at_campus_query.c.used,
    )).select_from(
        created_query
        .join(used_original_campus_query, and_(
            created_query.c.campus_id ==
            used_original_campus_query.c.campus_id,
            created_query.c.year == used_original_campus_query.c.year
        ))
        .join(used_at_campus_query, and_(
            created_query.c.campus_id == used_at_campus_query.c.campus_id,
            created_query.c.year == used_at_campus_query.c.year
        ))
    )

    gift_certificate_data = db.session.execute(gift_certificate_query)

    def generate_report():
        yield ("Campus", "Year", "Total", "Amount created",
               "Total amount remaining")
        for cid, group in groupby(gift_certificate_data, itemgetter(1)):
            cumulative_created = 0
            cumulative_used_original = 0
            for (campus_name, cid, year, created_amount, used_by_original,
                    used_by_use) in group:
                cumulative_created += created_amount
                cumulative_used_original += used_by_original
                yield (
                    campus_name,
                    str(year),
                    str(used_by_use),
                    str(created_amount),
                    str(cumulative_created - cumulative_used_original),
                )

    return csv_from_rows(generate_report())


def number_of_events_report(studios, start_date, end_date, period_label):
    schedules = db.session.query(models.Schedule)\
        .filter(
            models.Schedule.is_an_event == True,
            models.Schedule.date >= start_date,
            models.Schedule.date <= end_date,
            or_(models.Schedule.deleted == False, models.Schedule.deleted == None)
        )\
        .order_by(
            models.Schedule.date.asc(),
            models.Schedule.time.asc(),
        )

    if studios:
        if len(studios) == 1:
            schedules = schedules.filter(models.Schedule.campus == studios[0])
        else:
            studio_ids = [x.id for x in studios]
            schedules = schedules.filter(models.Schedule.campus_id.in_(studio_ids))

    def generate_report():
        yield (period_label, '')
        yield ("Date", "Times", "Class", "Pub/Priv/Event",
               "Studio(s)", "Spaces", "Avail", "Wait", "Teachers", "Assistants",
               "Comments")

        for schedule in schedules:
            yield (
                schedule.date.strftime("%a %-m/%d"),
                schedule.time_range,
                schedule.cls.abbr,
                "Public" if schedule.is_public else "Private",
                schedule.campus.domain,
                schedule.spaces if not schedule.is_an_event else "",
                (schedule.remaining_spaces()
                    if not schedule.is_an_event else ""),
                len(schedule.waitlists),
                ", ".join(teacher.user.first_name
                          for teacher in schedule.teachers),
                ", ".join(unicode(assistant) for assistant in schedule.assistants),
                schedule.comments,
            )
    return csv_from_rows(generate_report())


def classes_and_occupancy_report(studio, start_date, end_date, period_label):
    filters = [
        models.Schedule.date >= start_date,
        models.Schedule.date <= end_date,
        or_(models.Schedule.deleted == False, models.Schedule.deleted == None)
    ]
    if studio is not None:
        filters.append(models.Schedule.campus == studio)

    private_count = db.session.query(models.Schedule)\
       .filter_by(is_public=False)\
       .filter_by(is_an_event=False)\
       .filter(*filters)\
       .count()

    public_schedules = db.session.query(models.Schedule)\
        .filter_by(is_public=True)\
        .filter_by(is_an_event=False)\
        .filter(*filters)

    public_count = public_schedules.count()
    total_count = public_count + private_count

    occupancy_rates = []
    for schedule in public_schedules.all():
        occupancy_rates.append(float(schedule.spaces - schedule.remaining_spaces()) / schedule.spaces)

    if occupancy_rates:
        average = sum(occupancy_rates) / len(occupancy_rates)
    else:
        average = 0

    average = average * 100
    average = "{0:.2f}".format(average)
    average = average + '%'

    def generate_report():
        yield (period_label, '')
        yield ("Number of Publics", "Number of Privates",
               "Total Number of Classes", "Average Occupancy Rate")
        yield(public_count, private_count, total_count, average)
    return csv_from_rows(generate_report())


def private_class_report(studios, start_date, end_date, period_label):
    schedules = db.session.query(models.Schedule)\
        .filter(
            models.Schedule.date >= start_date,
            models.Schedule.date <= end_date,
            models.Schedule.is_public == False,
            or_(models.Schedule.deleted == False, models.Schedule.deleted == None)
        )\
        .order_by(
            models.Schedule.date.asc(),
            models.Schedule.time.asc(),
        )

    if studios:
        if len(studios) == 1:
            schedules = schedules.filter(models.Schedule.campus == studios[0])
        else:
            studio_ids = [x.id for x in studios]
            schedules = schedules.filter(models.Schedule.campus_id.in_(studio_ids))


    def generate_report():
        yield (period_label, '')
        yield ("Date", "Time", "Class", "Teachers", "Studio", "Assistants",
               "Contact Name", "Contact Email", "Contact Phone", "Company Name",
               "Reason for Event", "Comments")

        for schedule in schedules:
            yield (
                schedule.date.strftime("%a %-m/%d"),
                schedule.formatted_time,
                schedule.cls.abbr,
                u", ".join(teacher.user.first_name
                          for teacher in schedule.teachers),
                schedule.campus.domain,
                u", ".join(unicode(assistant) for assistant in schedule.assistants),
                schedule.contact_name,
                schedule.contact_email,
                schedule.contact_phone,
                schedule.company_name,
                schedule.event_reason,
                schedule.comments,
            )
    return csv_from_rows(generate_report())


def classes_taught_report(cls, studios, start_date, end_date, period_label):
    schedules = db.session.query(models.Schedule)\
        .filter(
            models.Schedule.cls == cls,
            models.Schedule.date >= start_date,
            models.Schedule.date <= end_date,
            or_(models.Schedule.deleted == False, models.Schedule.deleted == None)
        )\
        .order_by(
            models.Schedule.date.asc(),
            models.Schedule.time.asc(),
        )

    if studios:
        if len(studios) == 1:
            schedules = schedules.filter(models.Schedule.campus == studios[0])
        else:
            studio_ids = [x.id for x in studios]
            schedules = schedules.filter(models.Schedule.campus_id.in_(studio_ids))

    def generate_report():
        yield (period_label, '')
        yield ("Date", "Time", "Class", "Abbrev", "Teacher", "Public/Private",
               "Studio", "Spaces", "Available", "Assistant", "Comments")
        for schedule in schedules:
            yield (
                schedule.date,
                schedule.formatted_time,
                schedule.cls.title,
                schedule.cls.abbr,
                ", ".join(
                    teacher.user.first_name for teacher in schedule.teachers),
                "Public" if schedule.is_public else "Private",
                schedule.campus.domain,
                schedule.spaces,
                schedule.remaining_spaces(),
                ", ".join(unicode(assistant) for assistant in schedule.assistants),
                schedule.comments,
            )
    return csv_from_rows(generate_report())


def newsletter_subscribers_report(studio, reasons, start_date, end_date, period_label):
    subscribers = db.session.query(models.Subscriber)\
        .filter(
            models.Subscriber.created >= start_date,
            models.Subscriber.created <= end_date,
        )\
        .group_by(models.Subscriber.subscribe_reason)\
        .order_by(models.Subscriber.created.asc())

    if studio is not None:
        subscribers = subscribers.filter(models.Subscriber.campus == studio)

    if reasons is not None:
        subscribers = subscribers.filter(models.Subscriber.subscribe_reason.in_(reasons))

    collected = []
    for subscriber in subscribers:
        subscribe_reason = models.Subscriber.SUBSCRIBE_REASON_CHOICES[subscriber.subscribe_reason]
        if subscribe_reason == 'bought_gc':
            if subscriber.last_gift_certificate_purchased and subscriber.last_gift_certificate_purchased.recipient_email:
                recipient = subscriber.last_gift_certificate_purchased.recipient_email
                #sender = subscriber.last_gift_certificate_purchased.sender_email
            else:
                recipient = 'unknown'
            collected.append([subscriber.subscribe_reason, subscriber.name, subscriber.email, subscriber.campus.name, recipient])
        else:
            collected.append([subscriber.subscribe_reason, subscriber.name, subscriber.email, subscriber.campus.name, 'N/A'])

    def generate_report():
        yield ("Reason", "Name", "Email", "Studio", "Recipient")
        for row in collected:
            yield row

    return csv_from_rows(generate_report())


def schedule_page_report(teacher, studios, start_date, end_date, period_label):
    schedules = db.session.query(models.Schedule)\
        .join(models.schedule_teachers)\
        .filter(
            models.schedule_teachers.c.teacher_id == teacher.user_id,
            models.Schedule.date >= start_date,
            models.Schedule.date <= end_date,
            or_(models.Schedule.deleted == False, models.Schedule.deleted == None)
        )\
        .order_by(
            models.Schedule.date.asc(),
            models.Schedule.time.asc(),
        )

    if studios:
        if len(studios) == 1:
            schedules = schedules.filter(models.Schedule.campus == studios[0])
        else:
            studio_ids = [x.id for x in studios]
            schedules = schedules.filter(models.Schedule.campus_id.in_(studio_ids))

    def generate_report():
        yield (teacher.user.first_name, period_label)
        yield ("Date", "Time", "Class", "Abbrev", "Teacher", "Public/Private",
               "Studio", "Spaces", "Available", "Assistant", "Comments")
        for schedule in schedules:
            yield (
                schedule.date,
                schedule.formatted_time,
                schedule.cls.title,
                schedule.cls.abbr,
                ", ".join(
                    teacher.user.first_name for teacher in schedule.teachers),
                "Public" if schedule.is_public else "Private",
                schedule.campus.domain,
                schedule.spaces,
                schedule.remaining_spaces(),
                ", ".join(unicode(assistant) for assistant in schedule.assistants),
                schedule.comments,
            )
        yield ("Total", schedules.count())
        yield ("Public",
               schedules.filter(models.Schedule.is_public == True).count())
        yield ("Private",
               schedules.filter(models.Schedule.is_public == False).count())
    return csv_from_rows(generate_report())


def sales_report(teacher, studio, item, start_date, end_date, period_label):
    products = db.session.query(
            models.Product, func.sum(models.ProductOrderItem.quantity))\
        .join(models.ProductOrderItem)\
        .join(models.ProductOrder)\
        .filter(
            models.ProductOrder.date_ordered >= start_date,
            models.ProductOrder.date_ordered <= end_date,
        )\
        .group_by(models.Product)\
        .order_by(models.Product.name.asc())

    if teacher is not None:
        products = products.filter(
            models.ProductOrder.sold_by_id == teacher.user_id)
    if studio is not None:
        products = products.filter(models.ProductOrder.campus == studio)
    #if method_of_payment:
    #    products = products.filter(models.ProductOrder.paid_with == method_of_payment)
    if item:
        products = products.filter(models.Product.name == item)

    if studio is None:
        products_by_studios = []
        for campus in models.Campus.query.all():
            products_by_studios.append("Studio: {}".format(campus.name))
            studio_products = products.filter(models.ProductOrder.campus == campus).all()
            if studio_products:
                products_by_studios.append(["Product", "Quantity"])
                for prod_tup in studio_products:
                    products_by_studios.append(prod_tup)
            else:
                products_by_studios.append('--No sales--')


    def generate_report():
        if teacher is not None:
            if studio is not None:
                yield ("{}'s Sales, {}".format(
                    teacher.user.first_name, studio.name),)
            else:
                yield ("{}'s Sales, by studio".format(
                    teacher.user.first_name),)
        elif studio is not None:
            yield ("Hipcooks {} Sales".format(studio.name),)
        else:
            yield ("All Hipcooks sales by studio",)

        yield (start_date.strftime("%c"), end_date.strftime("%c"))


        if studio is not None:
            for product, count in products:
                yield (product.name, count)
        else:
            for row in products_by_studios:
                if type(row) == str or type(row) == unicode:
                    yield (row, '-----')
                else:
                    if hasattr(row[0], 'name'):
                        yield (row[0].name, row[1])
                    else:
                        yield (row[0], row[1])

    return csv_from_rows(generate_report())


def sales_of_the_day_report(teacher_value, studio, start_date, end_date, period_label):
    products = db.session.query(
            models.User, models.Campus, models.Product, models.ProductOrder,
            models.ProductOrderItem,
        )\
        .select_from(models.ProductOrder)\
        .outerjoin(models.User, models.User.id == models.ProductOrder.sold_by_id)\
        .join(models.Campus)\
        .join(models.ProductOrderItem,
              models.ProductOrderItem.productsale_id ==
              models.ProductOrder.id)\
        .join(models.Product,
              models.Product.id == models.ProductOrderItem.product_id)\
        .filter(
            models.ProductOrder.date_ordered >= start_date,
            models.ProductOrder.date_ordered <= end_date,
        )\
        .order_by(
            models.ProductOrder.date_ordered,
            models.ProductOrder.id,
        )

    if teacher_value == forms.SalesOfTheDayReportForm.ONLINE_SALES:
        products = products.filter(models.ProductOrder.sold_by_id == None)
    elif teacher_value != forms.SalesOfTheDayReportForm.ALL_SALES:
        products = products.filter(
            models.ProductOrder.sold_by_id == int(teacher_value))
    if studio is not None:
        products = products.filter(models.ProductOrder.campus == studio)

    def generate_report():
        yield ("Name", "Studio", "Date", "Time", "Amount", "Paid With", "Sale")
        for order, group in groupby(products, itemgetter(3)):
            items = []
            for (user, studio, product, order, item) in group:
                items.append("{}: {}".format(product.name.encode('utf8', 'ignore'), item.quantity))
            yield (
                user.first_name if user is not None else "Online",
                studio.name,
                order.date_ordered.date(),
                order.date_ordered.time().strftime("%I:%M %p"),
                format(order.total_paid, "0.2f"),
                order.paid_with,
                "\n".join(items),
            )
    return csv_from_rows(generate_report())


def inventory_adjustments_report(studio, product, reason, start_date, end_date, period_label):
    logs = db.session.query(models.ProductInventoryItem)\
                     .filter(models.ProductInventoryItem.date_stocked >= start_date,
                             models.ProductInventoryItem.date_stocked <= end_date)
    if studio:
        logs = logs.filter(models.ProductInventoryItem.campus_id == studio.id)

    if product:
        logs = logs.join(models.Product).filter(models.Product.name == product)

    if reason != "None":
        logs = logs.filter(models.ProductInventoryItem.reason == reason)

    def generate_report():
        yield (unicode(start_date), unicode(end_date))
        yield ("Date", "Product", "Type", "Studio", "Adjustment Amount", "Reason", "Transferred To")
        for log in logs:
            if log.reason == 1:
                yield (log.date_stocked, log.product.name, log.product.type, log.campus.name, log.quantity, 'Transfer To', log.dest_campus.name)
            else:
                yield (log.date_stocked, log.product.name, log.product.type, log.campus.name, log.quantity, log.reason_str, '')

    return csv_from_rows(generate_report())
