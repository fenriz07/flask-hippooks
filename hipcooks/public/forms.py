from flask.ext.wtf import Form, RecaptchaField
from wtforms import (validators, TextField, PasswordField, SelectField,
                     BooleanField, TextAreaField, ValidationError, Field,
                     SelectMultipleField, IntegerField, RadioField, FormField,
                     SubmitField)
from wtforms.form import Form as NonCSRFForm
from wtforms.widgets import CheckboxInput, HiddenInput, TextInput
from wtforms.validators import StopValidation
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from hipcooks import db, models, auth
from datetime import date
import us
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound


def validate_raw_password(form, field):
    if (field.data != form.retype_password.data):
        raise ValidationError("Passwords don't match")
    elif not (auth.is_legal_password(field.data) or field.data == ""):
        raise ValidationError("Password too short")


class SignInForm(Form):
    email = TextField("Email", [validators.email()])
    password = PasswordField("Password", [validators.required()])


class ForgotPasswordForm(Form):
    email = TextField("Email", [validators.email()])


class RegisterForm(Form):
    first_name = TextField("First Name", [validators.required()])
    last_name = TextField("Last Name", [validators.required()])
    phone = TextField("Phone Number", [validators.required()])
    email = TextField("Email", [validators.email()])
    raw_password = PasswordField("Password", [validators.required()])
    retype_password = PasswordField("Retype Password", [validators.required()])

    validate_raw_password = validate_raw_password

    def validate_email(form, field):
        if db.session.query(func.count(models.User))\
               .filter(models.User.username == field.data)\
               .scalar():
            raise ValidationError("Email already exists")


class UpdateAccountInfoForm(Form):
    first_name = TextField("First Name", [validators.required()])
    last_name = TextField("Last Name", [validators.required()])
    phone = TextField("Phone Number", [validators.required()])
    email = TextField("Email", [validators.email()])
    raw_password = PasswordField("Password")
    retype_password = PasswordField("Retype Password")
    subscriber = SelectField("Active Newsletter Subscription", choices=(
        ("True", "Yes"),
        ("", "No"),
    ))

    validate_raw_password = validate_raw_password

    def validate_on_submit(self, user):
        if not super(UpdateAccountInfoForm, self).validate_on_submit():
            return False
        if user.is_duplicate_with(self.email.data):
            self.email.errors.append("Email already exists")
            return False
        return True

    @classmethod
    def new(cls, formdata, user, newsletter):
        if formdata:
            return UpdateAccountInfoForm(formdata)
        form = UpdateAccountInfoForm(obj=user)
        print newsletter
        if newsletter is None:
            form.subscriber.data = ""
        else:
            form.subscriber.data = "True" if newsletter.active else ""
        return form


class ScheduleForm(Form):

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        guest_choices = [(0, "Just Me!")]
        remaining_spaces = kwargs.get('remaining_spaces')
        if remaining_spaces > 1:
            for x in range(1, min(4, remaining_spaces)):
                guest_choices.append((x, str(x + 1) + ' people'))
        self.guests.choices = guest_choices

    guests = SelectField("How many spots would you like?", coerce=int)
    cancellation_policy = BooleanField(
        "I've read and agree to the <a id='cancel_link' href='/cancellation-policy'>cancellation policy</a>",
        [validators.required()])
    comments = TextField("Comments")
    submit = SubmitField()

    def validate(self):
        if not self.submit.data:
            return False
        return super(ScheduleForm, self).validate()


class SchedulingSignInForm(SignInForm, ScheduleForm):
    pass


class SchedulingRegisterForm(RegisterForm, ScheduleForm):
    pass


class PrivateClassRequestForm(Form):
    name = TextField("Name", [validators.required()])
    email = TextField("Email", [validators.email()])
    phone = TextField("Phone", [validators.required()])
    dates = TextAreaField("Dates requesting", [validators.required()])
    menus = TextAreaField("Menu(s) you'd like", [validators.required()])
    type = TextField("Type of event", [validators.required()])
    contact = SelectMultipleField(option_widget=CheckboxInput(), choices=(
            ("contact_phone", "Contact by Phone"),
            ("contact_email", "Contact via Email"))
    )
    recaptcha = RecaptchaField()

    def validate_contact(form, field):
        if not form.contact.data:
            field.errors.append("At least one contact method is required")


class GiftCertificateMailingInfoForm(Form):
    name_on_envelope = TextField("Name on Envelope", [validators.required()])
    street_address = TextField("Street Address", [validators.required()])
    city = TextField("City", [validators.required(),
                              validators.length(max=100)])
    state = TextField("State", [validators.required(),
                                validators.length(max=2)])
    zip_code = TextField("Zip", [validators.required(),
                                 validators.length(max=10)])


class GiftCertificateForm(Form):
    DELIVERY_CHOICES = (
        (str(models.GiftCertificate.DELIVER_EMAIL_ME),
            "Email me the Gift Certificate"),
        (str(models.GiftCertificate.DELIVER_EMAIL_OTHER),
            "Email the recipient the Gift Certificate (and forward me a "
            "copy)."),
        (str(models.GiftCertificate.DELIVER_MAIL),
            "Pop it in the mail! The Gift Certificate will arrive within "
            "5-7 business days.")
    )
    delivery_method = RadioField(choices=DELIVERY_CHOICES)
    sender_name = TextField("Your name", [validators.required()])
    sender_email = TextField("Your email", [validators.email()])
    sender_phone = TextField("Your phone", [validators.required()])
    campus_id = QuerySelectField("Location", query_factory=lambda: models.Campus.query)
    amount_to_give = IntegerField("Amount giving", [validators.required()])
    recipient_name = TextField("Recipient name", [validators.required()])
    recipient_email = TextField("Recipient email", [validators.email()])
    message = TextField("Message")
    agreed = BooleanField(validators=[validators.required()])

    def validate_with_mailing_info(self, mailing_info_form):
        if self.validate_on_submit():
            if not self.needs_mailing_info:
                mailing_info_form.name_on_envelope.data = None
                mailing_info_form.street_address.data = None
                mailing_info_form.city.data = None
                mailing_info_form.state.data = None
                mailing_info_form.zip_code.data = None
                return True
            else:
                return mailing_info_form.validate()
        return False

    @property
    def needs_mailing_info(self):
        return (self.delivery_method.data ==
                str(models.GiftCertificate.DELIVER_MAIL))


class MarketFilterForm(Form):
    SEARCH_BY_CHOICES = ([("all", "All")] +
                         models.ResourcesMarket.MARKET_DATA.values())

    search_by = SelectField("SEARCH BY:", choices=SEARCH_BY_CHOICES)


class AddressForm(Form):
    name = TextField("Name", [validators.required()])
    address_line_1 = TextField("Address", [validators.required()])
    address_line_2 = TextField("", [])
    city = TextField("City", [validators.required()])
    state = SelectField("State", [validators.required()], choices=[(s.abbr, s.name,) for s in us.states.STATES_AND_TERRITORIES])
    zip_code = TextField("ZIP", [validators.required(), validators.regexp(r"^\d{5}(?:-?\d{4})?$", message="Please enter a valid zip code.")])


class PaymentForm(Form):
    cc_number = TextField("Card Number", [validators.regexp(r"^\d{12,16}$", message="Please enter a correct credit card number (12-16 numbers).")])
    cc_exp_month = SelectField(choices=[(str(i), "{:02d}".format(i)) for i in range(1, 13)])
    cc_exp_year = SelectField()
    cc_vv = TextField("CVC", [validators.regexp(r"^\d{3,4}$", message="Please enter a correct verification code (3-4 numbers).")])

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        thisyear = int(date.today().strftime("%Y"))
        year_choices = [(str(i), str(i)) for i in reversed(range(thisyear, thisyear + 6, ))]

        self.cc_exp_year.choices = year_choices


class CheckoutForm(Form):
    name = TextField("Name", [validators.required()])
    email = TextField("Email", [validators.email()])
    phone = TextField("Phone", [validators.required()])
    billing_address = FormField(AddressForm)


class NonShippingCheckoutForm(CheckoutForm):
    payment = FormField(PaymentForm)

    def remove_payment_form(self):
        del self.payment


class ShippingCheckoutForm(CheckoutForm):
    shipping_address = FormField(AddressForm)
    payment = FormField(PaymentForm)

    def remove_payment_form(self):
        del self.payment


class StoreProductForm(Form):
    quantity = IntegerField([validators.required()])

    def validate_with_quantity(self, count):
        return self.validate_on_submit() and self.quantity.data <= count


class ReservationLookupForm(Form):
    code = TextField("Reservation code:")

    def validate_code(form, field):
        try:
            order = db.session.query(models.ScheduleOrder)\
                .filter_by(code=field.data)\
                .one()
            if order.in_past:
                raise NoResultFound
        except NoResultFound:
            raise ValidationError("Reservation code not found")


class ContactForm(Form):
    name = TextField("Name", [validators.required()])
    email = TextField("Email", [validators.email()])
    note = TextAreaField("Jot a Quick Note")


class ForgotPasswordResetForm(Form):
    raw_password = PasswordField("Password")
    raw_password_confirm = PasswordField("Confirm Password")

    def validate_raw_password_confirm(form, field):
        if form.raw_password.data != field.data:
            raise ValidationError("Passwords don't match")
