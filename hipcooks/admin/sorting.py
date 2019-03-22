from sqlalchemy.sql.expression import func, column
from hipcooks import models


def _sort(*columns):
    def sorter(query, order):
        if order == "desc":
            final_columns = map(lambda c: c.desc(), columns)
        else:
            final_columns = columns
        return query.order_by(*final_columns)
    return sorter


name_sort = _sort(func.ltrim(models.User.first_name),
                  func.ltrim(models.User.last_name))
last_name_sort = _sort(func.ltrim(models.User.last_name))
username_sort = _sort(func.ltrim(models.User.username))
email_sort = _sort(func.ltrim(models.User.email))
active_sort = _sort(func.ltrim(models.Assistant.active))
teacher_mobile_sort = _sort(func.ltrim(models.Teacher.mobile_phone))
assistant_mobile_sort = _sort(func.ltrim(models.Assistant.mobile_phone))


staff_criteria = {
    "name": name_sort,
    "last_name": last_name_sort,
    "username": username_sort,
    "email": email_sort,
    "mobile_phone": teacher_mobile_sort,
}

assistant_criteria = {
    "name": name_sort,
    "last_name": last_name_sort,
    "username": username_sort,
    "email": email_sort,
    "mobile_phone": assistant_mobile_sort,
    "active": active_sort,
}

schedule_criteria = {
    "date": _sort(models.Schedule.date),
    "time": _sort(models.Schedule.time),
    "abbr": _sort(models.Class.abbr),
    "studio": _sort(models.Campus.name),
    "spaces": _sort(models.Schedule.spaces),
}

gift_certificate_criteria = {
    "sender_name": _sort(models.GiftCertificate.sender_name),
    "sender_email": _sort(models.GiftCertificate.sender_email),
    "recipient_name": _sort(models.GiftCertificate.recipient_name),
    "created": _sort(models.GiftCertificate.created),
    "date_sent": _sort(models.GiftCertificate.date_sent),
    "amount_remaining": _sort(column("amount_remaining")),
    "amount_to_give": _sort(models.GiftCertificate.amount_to_give),
    "campus": _sort(models.Campus.order),
    "gift_code": _sort(models.GiftCertificate.code),
    "giftcard": _sort(models.GiftCertificate.giftcard),
    "paid_with": _sort(models.GiftCertificate.paid_with),
}

subscriber_criteria = {
    "email": _sort(models.Subscriber.email),
    "name": _sort(models.Subscriber.name),
    "created": _sort(models.Subscriber.created),
}

product_criteria = {
    "name": _sort(models.Product.name),
    "type": _sort(models.Product.type),
    "price": _sort(models.Product.price),
    "available_to_ship": _sort(models.Product.available_to_ship),
    "cost_to_ship": _sort(models.Product.cost_to_ship),
}

product_inventory_criteria = {
    "studio": _sort(models.Campus.name),
    "name": _sort(models.Product.name),
    "type": _sort(models.Product.type),
    "stock": _sort(models.ProductInventory.quantity_stocked),
    "price": _sort(models.Product.price),
}

product_inventory_log_criteria = {
    "date": _sort(models.ProductInventoryItem.date_stocked),
}

sales_criteria = {
}
