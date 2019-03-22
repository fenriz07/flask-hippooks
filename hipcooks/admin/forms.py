from flask.ext.wtf import Form
import wtforms
from wtforms import (TextField, StringField, PasswordField, validators,
                     SelectField, TextAreaField, ValidationError, widgets,
                     SelectMultipleField, BooleanField, HiddenField,
                     SubmitField, IntegerField, DateField, FileField,
                     DecimalField, RadioField, FormField)
from wtforms.ext.sqlalchemy.fields import (
    QuerySelectField, QuerySelectMultipleField)
from flask_wtf.file import FileField as FlaskFileField
from wtforms.widgets import html_params, HTMLString, HiddenInput
from hipcooks import models, db
#from sqlalchemy.sql.expression import cast
#from sqlalchemy import types
from datetime import date, time, datetime
from dateutil.relativedelta import relativedelta
import itertools


def add_html_class(kwargs, html_class):
    html_classes = kwargs.pop("class", "") or kwargs.pop("class_", "")
    kwargs["class"] = "{} {}".format(html_class, html_classes)


class ChosenSelectWidget(widgets.Select):
    def __call__(self, field, **kwargs):
        add_html_class(kwargs, "chosen-select")
        return super(ChosenSelectWidget, self).__call__(field, **kwargs)


class DatePickerWidget(widgets.TextInput):
    def __call__(self, field, **kwargs):
        add_html_class(kwargs, "date")
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class RichEditorWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        add_html_class(kwargs, "rich-editor")
        kwargs["rows"] = 15
        return super(RichEditorWidget, self).__call__(field, **kwargs)


class DisabledTextWidget(widgets.TextInput):
    def __call__(self, field, **kwargs):
        return super(DisabledTextWidget, self).__call__(
            field, disabled=True, **kwargs)


PAID_WITH_CATEGORIES = (
    ("None", "None"),
    (models.GiftCertificate.CATEGORY_CC, "Credit Card"),
    (models.GiftCertificate.CATEGORY_CALL_IN, "Call-in CC"),
    (models.GiftCertificate.CATEGORY_FREEBIE, "Freebie"),
    (models.GiftCertificate.CATEGORY_ASSISTANT, "Assistant"),
    (models.GiftCertificate.CATEGORY_DONATION, "Donation"),
    (models.GiftCertificate.CATEGORY_CHECK, "Check"),
    (models.GiftCertificate.CATEGORY_CASH, "Cash"),
    (models.GiftCertificate.CATEGORY_MAKEUP, "Makeup"),
    (models.GiftCertificate.CATEGORY_PRIVATE, "Private Class"),
    (models.GiftCertificate.CATEGORY_GROUPON, "Groupon"),
)


PAID_WITH_CATEGORIES_SMALL = (
    (models.GiftCertificate.CATEGORY_CC, "Credit Card"),
    (models.GiftCertificate.CATEGORY_CASH, "Cash"),
    (models.GiftCertificate.CATEGORY_CHECK, "Check"),
)


class MultiCheckboxWidget(object):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('type', 'checkbox')
        field_id = kwargs.pop('id', field.id)
        html = [u'<ul {}>'.format(html_params(id=field_id, class_=""))]
        for value, label, checked in field.iter_choices():
            choice_id = u'{}-{}'.format(field_id, value)
            options = dict(kwargs, name=field.name, value=value, id=choice_id)
            if checked:
                options['checked'] = 'checked'
            html.append(u'<li><input {} /> '.format(html_params(**options)))
            html.append(u'<label for="{}">{}</label></li>'.format(field_id, label))
        html.append(u'</ul>')
        return HTMLString(''.join(html))


class ReadonlyTextField(TextField):
    def __call__(self, *args, **kwargs):
        kwargs.setdefault('readonly', True)
        return super(ReadonlyTextField, self).__call__(*args, **kwargs)


class LoginForm(Form):
    username = TextField("Login", [validators.required()])
    password = PasswordField("Password", [validators.required()])

class ChangePasswordForm(Form):
    raw_password = PasswordField("Password")
    raw_password_confirm = PasswordField("Confirm Password")

    def validate_raw_password_confirm(form, field):
        if form.raw_password.data != field.data:
            raise ValidationError("Passwords don't match")


class ClassForm(Form):
    order = IntegerField("Order", [validators.required()])
    title = TextField("Title", [validators.required()])
    abbr = TextField("Abbr", [validators.required()])
    #color_code = TextField("Color Code", [])
    description = TextAreaField("Description")
    menu = TextAreaField("Menu")
    wine = TextAreaField("To taste")
    knife_level = SelectField(
        "Knife level", choices=models.Class.KNIFE_LEVELS.items())
    veggie_level = SelectField(
        "Veggie level", choices=models.Class.VEGGIE_LEVELS.items())
    dairy_level = SelectField(
        "Dairy level", choices=models.Class.DAIRY_LEVELS.items())
    wheat_level = SelectField(
        "Wheat level", choices=models.Class.WHEAT_LEVELS.items())
    cost_override = IntegerField("Cost Override", [validators.optional()])


class RecipeForm(Form):
    title = TextField("Title", [validators.optional()])
    intro = TextAreaField("Intro", [validators.optional()], widget=RichEditorWidget())
    serves = TextField("Serves", [validators.optional()])
    ingredients = TextAreaField("Ingredients", [validators.optional()], widget=RichEditorWidget())
    instructions = TextAreaField("Instructions", [validators.optional()], widget=RichEditorWidget())
    recipe_order = HiddenField()


class RecipeSetForm(Form):
    class_name = TextField("Class", widget=DisabledTextWidget())
    intro = TextAreaField('Intro', widget=RichEditorWidget())
    last_updated = TextField("Last Updated", widget=DisabledTextWidget())


class RecipeEmailForm(Form):
    from_ = TextField(widget=DisabledTextWidget())
    to = TextAreaField()
    subject = TextField()

    def __init__(self, cls, *args, **kwargs):
        subject = "Hipcooks Class Recipes: {}".format(cls.title)
        super(RecipeEmailForm, self).__init__(
            *args, subject=subject, **kwargs)


class AssistantSignupEmailForm(Form):
    to = TextField("To", widget=DisabledTextWidget())
    subject = TextField()
    body = TextField("Body", widget=RichEditorWidget())


class SetupForm(Form):
    @staticmethod
    def new(form_data, setup_obj):
        form = SetupForm(form_data, setup_obj)
        form.csrf_enabled = False
        if form_data:
            form.rounds = [
                SetupRoundForm.from_form_data(form_data, round)
                for round in range(int(form_data["rounds"]))
            ]
        elif setup_obj is not None:
            form.rounds = [
                SetupRoundForm.from_obj(round) for round in setup_obj.rounds
            ]
        else:
            form.rounds = [SetupRoundForm.from_nothing() for i in range(3)]
        return form

    def validate(self):
        return (
            super(SetupForm, self).validate() and
            all(round.validate() for round in self.rounds)
        )

    class_name = TextField("Class", widget=DisabledTextWidget())
    pre_prep = TextField("Pre Prep", widget=RichEditorWidget())
    prep = TextField("Prep", widget=RichEditorWidget())
    setup = TextField("Setup", widget=RichEditorWidget())
    class_intro = TextField("Class Intro", widget=RichEditorWidget())
    menu_intro = TextField("Menu Intro", widget=RichEditorWidget())


class SetupRoundForm(Form):
    @staticmethod
    def from_form_data(form_data, round_num):
        form = SetupRoundForm(
            formdata=None,
            round_intro=form_data["{}-round_intro".format(round_num)],
            round_number=round_num,
        )
        form.csrf_enabled = False
        form.points = [
            SetupRoundPointForm(None, teaching_point=tp, action_point=ap)
            for tp, ap in zip(
                form_data.getlist("{}-teaching_point".format(round_num)),
                form_data.getlist("{}-action_point".format(round_num))
            )
        ]
        return form

    @staticmethod
    def from_obj(round):
        form = SetupRoundForm(
            round_intro=round.round_intro,
            round_number=round.round_number
        )
        form.points = [SetupRoundPointForm(None, obj=p) for p in round.points]
        return form

    @staticmethod
    def from_nothing():
        form = SetupRoundForm(data={})
        form.points = [SetupRoundPointForm(None, data={})]
        return form

    def validate(self):
        return (
            super(SetupRoundForm, self).validate() and
            all(point.validate() for point in self.points)
        )

    round_intro = TextAreaField("Round Setup", widget=RichEditorWidget())
    round_number = IntegerField([validators.required()], widget=HiddenInput())


class ShoppingListInstanceItemForm(Form):

    @staticmethod
    def category_choices():
        return [(key, value) for key, value in models.ShoppingListItem.CATEGORIES.iteritems()]

    @staticmethod
    def class_choices():
        return [(x.id, x.abbr) for x in models.Class.query.all()]

    def __init__(self, *args, **kwargs):
        super(ShoppingListInstanceItemForm, self).__init__(*args, **kwargs)
        self.category.choices = self.category_choices()
        self.item_class.choices = self.class_choices()

    campus = QuerySelectField(query_factory=lambda: models.Campus.query)
    item_class = SelectField(validators=[validators.optional()], coerce=int)
    category = SelectField(validators=[validators.optional()])
    name = TextField("name", [validators.required()])
    quantity = IntegerField("Quantity", [validators.required()])
    unit = TextField("Unit", [validators.optional()])
    notes = TextField("Notes", [validators.optional()])
    market = TextField("Market", [validators.required()])


class SetupRoundPointForm(Form):
    def __init__(self, *args, **kwargs):
        super(SetupRoundPointForm, self).__init__(*args, **kwargs)
        self.csrf_enabled = False

    teaching_point = TextAreaField("Teaching Points", widget=RichEditorWidget(), validators=[])
    action_point = TextAreaField("Action Points", widget=RichEditorWidget(), validators=[])


class ShoppingListForm(Form):
    check = TextAreaField("Check the Following:", widget=RichEditorWidget())


class TeacherEditForm(Form):
    username = TextField("Username", [validators.required()])
    raw_password = PasswordField("Password")
    first_name = TextField("First Name", [validators.required()])
    last_name = TextField("Last Name")
    email = TextField("Email", [validators.email()])
    bio = TextAreaField("Bio", widget=RichEditorWidget())
    upload_pic = FileField("Picture")
    mobile_phone = TextField("Mobile Number")
    street = TextField("Address")
    city = TextField("City")
    state = TextField("State")
    zip_code = TextField("Zip Code")
    ssn = TextField("SSN")
    birthdate = DateField("Birthdate",format='%m/%d/%Y', validators=(validators.Optional(),))
    ic_agreement = DateField("IC Agreement",format='%m/%d/%Y', validators=(validators.Optional(),))
    active = BooleanField(default=True)

    def validate_with_user(self, teacher, user):
        if not self.validate_on_submit():
            return False
        elif user.is_duplicate_with(self.username.data, self.email.data):
            self.username.errors.append("Duplicate username or email")
            return False
        elif teacher.is_duplicate_with(self.username.data, self.email.data):
            self.username.errors.append("Duplicate username or email")
            return False
        return True


class AssistantEditForm(Form):
    username = TextField("Username", [validators.required()])
    raw_password = PasswordField("Password")
    email = TextField("Email", [validators.email()])
    first_name = TextField("First Name", [validators.required()])
    last_name = TextField("Last Name")
    mobile_phone = TextField("Phone Number")
    active = BooleanField("Active")
    classes = IntegerField("Classes",default=0)
    credits = IntegerField("Credits",default=0)

    def validate_with_user(self, assistant, user):
        if not self.validate_on_submit():
            return False
        elif user.is_duplicate_with(self.username.data, self.email.data):
            self.username.errors.append("Duplicate username or email")
            return False
        elif assistant.is_duplicate_with(self.username.data, self.email.data):
            self.username.errors.append("Duplicate username or email")
            return False
        return True


class BulkEmailForm(Form):
    from_email = ReadonlyTextField("From")
    emails = TextAreaField("Recipients")
    subject = TextField("Subject")
    body = TextField("Body", widget=RichEditorWidget())


class CampusAssistantEmailForm(BulkEmailForm):
    campus = QuerySelectField("Studio", [validators.required()],
                              widget=ChosenSelectWidget(),
                              query_factory=lambda: models.Campus.query,
                              allow_blank=True, blank_text="Select a studio",
                              get_label="name")


class GiftCertificateEmailForm(Form):
    email_type = HiddenField()
    from_email = ReadonlyTextField("From")
    recipient = TextField("Recipient", [validators.email()])
    date_sent = DateField("Date Sent", [validators.optional()], format="%m/%d/%Y")
    subject = TextField("Subject")
    body = TextField("Body", widget=RichEditorWidget())
    pdf = FlaskFileField("PDF")
    receipt = FlaskFileField("Receipt")

time_choices = [("{}:{:0<2}".format(*time_info),
                 time(*time_info).strftime("%I:%M %p"))
                for time_info in
                itertools.product(range(10, 20), (0, 30))]


class ScheduleEditForm(Form):
    campus = QuerySelectField("Studio", [validators.required()],
                              widget=ChosenSelectWidget(),
                              query_factory=lambda: models.Campus.query,
                              allow_blank=True, blank_text="Select a studio",
                              get_label="name")
    cls = QuerySelectField("Class", [validators.required()],
                           widget=ChosenSelectWidget(),
                           query_factory=lambda: models.Class.query.order_by(models.Class.abbr.asc()),
                           allow_blank=True, blank_text="Select a class",
                           get_label="abbr")
    is_public = BooleanField("Is public", default=True)
    is_an_event = BooleanField("Is an event")

    # Fields for private classes and events
    contact_name = TextField('Contact name')
    contact_email = TextField('Contact email', [validators.Optional(), validators.email()])
    contact_phone = TextField('Contact phone')
    company_name = TextField('Company name')
    event_reason = SelectField(u'Event reason', choices=[('Birthday','Birthday'),('Bridal/Baby Shower','Bridal/Baby Shower'),('Corporate','Corporate'),('Open House','Open House'),('Holiday Party','Holiday Party'),('Assistant Party','Assistant Party'),('Staff Meeting','Staff Meeting'),('Assistant Class','Assistant Class'),('Other','Other: Please fill in')])

    date = DateField("Date", [validators.required()], format="%m/%d/%Y")
    time_info = SelectField(
        "Time", [validators.required()], choices=time_choices)
    duration = DecimalField("Duration", [validators.required()])
    spaces = IntegerField("Spaces", [validators.required()])
    comments = TextAreaField("Comments")
    teachers = QuerySelectMultipleField(
        "Teachers", [validators.required()],
        widget=ChosenSelectWidget(multiple=True),
        query_factory=lambda: models.Teacher.query.join(models.User).order_by(models.User.first_name.asc()),
        get_label=lambda t: t.user.first_name)
    assistants = QuerySelectMultipleField(
        "Assistants",
        widget=ChosenSelectWidget(multiple=True),
        query_factory=models.Assistant.query_active,
        get_label=lambda t: unicode(t.user))
    #deleted = BooleanField("Deleted")

    def studio_teacher_map(self):
        studio_teachers = {}
        for studio in models.Campus.query.all():
            studio_teachers[studio.id] = studio.teachers
        return studio_teachers

    def studio_assistant_map(self):
        studio_assistants = {}
        for studio in models.Campus.query.all():
            studio_assistants[studio.id] = studio.assistants
        return studio_assistants


class StudioEditForm(Form):
    domain = TextField("Domain Root", [validators.required()])
    name = TextField("Name", [validators.required()])
    abbreviation = TextField("Abbreviation", [validators.required()])
    tab_name = TextField("Tab Name", [])
    order = IntegerField("Sort Order",[validators.required()])
    facebook_url = TextField("Facebook url", [validators.required()])
    instagram_url = TextField("Instagram url", [validators.required()])
    google_plus_url = TextField("Google+ url", [validators.required()])
    yelp_url = TextField("Yelp url", [validators.required()])
    color_code = TextField("Color Code", [])
    class_size = IntegerField("Class Size", [validators.required()])
    image = FileField("Image")
    start_time = SelectField(
        "Default Start Time", [validators.required()], choices=time_choices)
    duration = DecimalField("Duration", [validators.required()])
    base_cost = DecimalField("Base Cost", [validators.required()])
    private_class_fee = DecimalField("Private Class Fee", [validators.required()])
    email = TextField("Email", [validators.email()])
    phone = TextField("Phone", [validators.required()])
    address = TextField("Address", [validators.required()])
    city = TextField("City", [validators.required()])
    state = TextField("State", [validators.required()])
    zipcode = TextField("Zip Code", [validators.required()])
    directions = TextAreaField(
        "Directions", [validators.required()], widget=RichEditorWidget())
    embed_url = TextField("Embedded map url", [validators.required()])
    sales_tax = DecimalField("Sales Tax", [validators.optional()])
    authorize_net_login = TextField("Authorize.net login", [validators.required()])
    authorize_net_tran_key = TextField("Authorize.net tran key", [validators.required()])
    class_in_session_body = TextField(
        "Class In Session Body", widget=RichEditorWidget())
    the_skinny_body = TextField(
        "The Skinny Body", widget=RichEditorWidget())
    private_class_page_text = TextField(
        "Private Class Page Text", widget=RichEditorWidget())
    private_class_page_policy_text = TextField(
        "Private Class Page Policy Text", widget=RichEditorWidget())

class GiftCertificateEditForm(Form):
    campus = QuerySelectField(
        "Studio", [validators.required()], widget=ChosenSelectWidget(),
        query_factory=lambda: models.Campus.query,
        blank_text="Select a studio", get_label="name")
    sender_name = TextField("Sender Name", [validators.required()])
    sender_email = TextField("Sender Email",
                             [validators.Optional(), validators.email()])
    sender_phone = TextField("Sender Phone Number")
    form_amount_remaining = DecimalField("Amount", [validators.required()])
    recipient_name = TextField("Recipient Name")
    recipient_email = TextField("Recipient Email",
                                [validators.Optional(), validators.email()])
    message = TextAreaField("Message")
    giftcard = BooleanField("Is Gift Card")
    date_sent = DateField("Date Sent", [validators.Optional()],
                          format="%m/%d/%Y", widget=DatePickerWidget())
    name_on_envelope = TextField("Name on envelope")
    street_address = TextField("Street Address")
    city = TextField("City")
    state = TextField("State")
    zip_code = TextField("Zip Code")
    code = TextField("Gift Code")
    paid_with = SelectField("Paid With", choices=PAID_WITH_CATEGORIES)
    expiration_date = DateField("Expiration Date", [validators.Optional()],
                                format="%m/%d/%Y", widget=DatePickerWidget())


class GiftCertificateBlockEditForm(Form):
    name = TextField("Block Name", [validators.required()])
    campus = QuerySelectField(
        "Studio", [validators.required()], widget=ChosenSelectWidget(),
        query_factory=lambda: models.Campus.query,
        blank_text="Select a studio", get_label="name")
    sender_name = TextField("Sender Name", [validators.required()])
    sender_email = TextField("Sender Email",
                             [validators.Optional(), validators.email()])
    sender_phone = TextField("Sender Phone Number")
    amount_to_give = IntegerField("Amount", [validators.required()])
    recipient_name = TextField("Recipient Name")
    message = TextField("Message")
    date_sent = DateField("Date Sent", [validators.Optional()],
                          format="%m/%d/%Y", widget=DatePickerWidget())
    paid_with = SelectField("Paid With", choices=PAID_WITH_CATEGORIES)
    expiration_date = DateField("Expiration Date", [validators.Optional()],
                                format="%m/%d/%Y", widget=DatePickerWidget())
    total_certs = IntegerField("Number", [validators.NumberRange(min=1, message="You must generate at least one certificate")])


class CampusSelectForm(Form):
    header_campuses = QuerySelectMultipleField(
                        "Studio", [validators.required()],
                        widget=MultiCheckboxWidget(),
                        get_label=lambda x: x.abbreviation
                    )


class ActiveFilterForm(wtforms.Form):
    FILTER_ACTIVE = "active"
    FILTER_INACTIVE = "inactive"
    ACTIVE_CHOICES = ((FILTER_ACTIVE, "Active"), (FILTER_INACTIVE, "Inactive"))

    filter_activity = SelectMultipleField(
        "Active", widget=MultiCheckboxWidget(), choices=ACTIVE_CHOICES,
        default=["active", "inactive"]
    )


class StaticContentEditForm(Form):
    CATEGORIES = (
        (models.StaticPage.CATEGORY_CONTENT, "Page Content"),
        (models.StaticPage.CATEGORY_PAGE, "Static Page"),
        (models.StaticPage.CATEGORY_EMAIL, "Email"),
    )

    path = TextField("Path", [validators.required()])
    description = TextField("Description", [validators.required()])
    title = TextField("Page Title", [validators.required()])
    email_subject = TextField("Email Subject")
    body = TextAreaField("Body", widget=RichEditorWidget())
    category = SelectField("Category", [validators.required()],
                           choices=CATEGORIES)


class SubscriberEditForm(Form):
    name = TextField("Name", [validators.required()])
    email = TextField("Email", [validators.required(), validators.email()])
    created = DateField("Date Added", format="%m/%d/%Y", widget=DatePickerWidget())
    subscribe_reason = TextField(widget=DisabledTextWidget())
    campus = QuerySelectField("Studio", [validators.required()],
                              widget=ChosenSelectWidget(),
                              query_factory=lambda: models.Campus.query,
                              allow_blank=True, blank_text="Select a studio",
                              get_label="name")


class ClassReportForm(Form):
    attendance_rating_list = SelectMultipleField(
                        "Everybody Here?",
                        [validators.required()],
                        choices=(
                            ("0", "All present and accounted for!"),
                            ("1", "No Shows"),
                            ("2", "I had extra people"),
                            ("4", "Someone sent another in their place"),
                            ("8", "Anybody interested in assisting?"),
                        ),
                        widget=MultiCheckboxWidget()
                    )

    class_rating = SelectField(
                        "Overall, how was your class?",
                        [validators.required()],
                        choices=models.ClassReport.CLASS_CHOICES.items()
                    )
    assistant_rating = SelectField(
                        "How rockin' was your assistant?",
                        [validators.required()],
                        choices=models.ClassReport.ASSISTANT_CHOICES.items()
                    )
    group_comments = TextAreaField("How was the group? Any standout students or stories?", [])
    food_comments = TextAreaField("How was the food? What menu items worked well, what didn't?", [])
    pacing_rating = RadioField(
                        "How was the overall pacing of the class?",
                        [validators.required()],
                        choices=models.ClassReport.PACING_CHOICES.items()
                    )
    pacing_comments = TextAreaField(
                        "Your challenges:",
                        [validators.required()]
                    )

    setup_review = TextAreaField(
                        """
You reviewed the prep, set up & teaching notes before class. Any suggestions to improve these? Do you have questions or need clarification so that you (& everyone!) can teach this class more better!
""",
                        []
                    )

    tasting_rating = RadioField(
                        "What tasting portions have you saved? We love to give compliments & comments!",
                        [validators.required()],
                        choices=models.ClassReport.TASTING_CHOICES.items()
                    )
    tasting_comments = TextAreaField(
                        "Tasting portions:",
                        []
                    )
    preprep_rating = RadioField(
                        "How was your pre-prep?",
                        [],
                        choices=models.ClassReport.PREPREP_CHOICES.items()
                    )
    preprep_comments = TextAreaField(
                        "(Alternatively, use this box to gush compliments)",
                        []
                    )

    ingredients_problems = RadioField(
                        "Any problems/issues with ingredients/amounts?",
                        [],
                        choices=(
                            ("0", "Nope"),
                            ("1", "Yup"),
                        )
                    )
    ingredients_comments = TextAreaField(
                        "List problems here (Also, list any extra ingredients worth noting)",
                        []
                    )

    breakage_rating = RadioField(
                        "Any breakages, burnt pans, broken equipment?",
                        [],
                        choices=models.ClassReport.BREAKAGE_CHOICES.items()
                    )
    breakage_comments = TextAreaField(
                        "(If a broken glass, list where/how)",
                        []
                    )
    sales_rating = RadioField(
                        "Here are your sales for the evening. Is all correct?",
                        [],
                        choices=models.ClassReport.SALES_CHOICES.items()
                    )
    sales_comments = TextAreaField(
                        "List sales thats need correcting here",
                        []
                    )


class ProductEditForm(Form):
    name = TextField("Name", [validators.required()])
    type = TextField("Type", [])
    image = FileField("Photo", [])
    thumbnail_image = FileField("Thumbnail Photo", [])
    price = DecimalField("Price")
    description = TextField("Description", [], widget=RichEditorWidget())
    available_to_ship = BooleanField("Available to ship", default=False)
    cost_to_ship = DecimalField("Cost to ship")
    row = IntegerField("Row", default=0)
    column = IntegerField("Column", default=0)
    splash_type = BooleanField("Show as \"splash\" type on store page", default=False)
    is_resource = BooleanField("Show as a resource", default=False)
    kitchen_row = IntegerField("Resource row", default=0)
    kitchen_column = IntegerField("Resource column", default=0)
    resource_name = TextField("Resource Name")


class TeacherSalesOrderForm(Form):
    studio = QuerySelectField(
        "Studio", [validators.required()],
        widget=ChosenSelectWidget(), get_label="name")
    sold_by = QuerySelectField(
        "Sold by", [validators.required()],
        widget=ChosenSelectWidget(), get_label="username")
    DISCOUNT_CHOICES = (
        ("0", "No"),
        ("5", "5%"),
        ("10", "10%"),
        ("15", "15%"),
        ("20", "20%"),
    )
    discount = SelectField("Discount", choices=DISCOUNT_CHOICES)
    paid_with = SelectField("Payment type", choices=models.ProductOrder.PAID_WITH_CHOICES)

    @classmethod
    def new(cls, campus_ids, *args, **kwargs):
        sale_info_form = cls(*args, **kwargs)
        sale_info_form.studio.query = models.Campus.query\
            .filter(models.Campus.id.in_(campus_ids))
        sale_info_form.sold_by.query = models.User.query\
            .join(models.Teacher)\
            .join(models.TeacherCampus)\
            .filter(models.TeacherCampus.campus_id.in_(campus_ids),models.Teacher.active==True)\
            .distinct()

        if not kwargs["sold_by"].is_superuser:
            sale_info_form.paid_with.choices = models.ProductOrder.PAID_WITH_CHOICES[0:4]

        return sale_info_form


class ReportDateForm(wtforms.Form):
    QUARTERS = (("0", "Q1"), ("1", "Q2"), ("2", "Q3"), ("3", "Q4"))
    MONTH_CHOICES = zip(map(str, range(1, 13)), range(1, 13))
    YEAR_CHOICES = zip(map(str, range(2008, date.today().year + 1)),
                       range(2008, date.today().year + 1))
    month_year_select = FormField(type("MonthYearForm", (wtforms.Form,), {
        "month": SelectField("Month", choices=MONTH_CHOICES, default=date.today().month),
        "year": SelectField("Year", choices=YEAR_CHOICES, default=date.today().year),
    }))
    if date.today().month in (1,2,3):
        q = "0"
    elif date.today().month in (4,5,6):
        q = "1"
    elif date.today().month in (7,8,9):
        q = "2"
    elif date.today().month in (10,11,12):
        q = "3"
    quarter_year_select = FormField(type("QuarterYearForm", (wtforms.Form,), {
        "quarter": SelectField("Quarter", choices=QUARTERS, default=q),
        "year": SelectField("Year", choices=YEAR_CHOICES, default=date.today().year),
    }))
    year_select = FormField(type("YearForm", (wtforms.Form,), {
        "year": SelectField("Year", choices=YEAR_CHOICES, default=date.today().year),
    }))
    custom_date_select = FormField(type("DateForm", (wtforms.Form,), {
        "custom_dates": TextField("Dates"),
    }))
    selection = HiddenField()

    @property
    def dates(self):
        selection = self.selection.data
        if selection == 'month_year':
            year = int(self.month_year_select.year.data)
            month = int(self.month_year_select.month.data)
            start = date(year, month, 1)
            end = date(year, month, 1) + relativedelta(months=1, days=-1)
            period_label = start.strftime('%B %Y')
        elif selection == 'quarter_year':
            year = int(self.quarter_year_select.year.data)
            quarter = int(self.quarter_year_select.quarter.data)
            start = date(year, quarter * 3 + 1, 1)
            end = date(year, quarter * 3 + 1, 1) + relativedelta(months=3, days=-1)
            period_label = 'Quarter {}'.format(quarter + 1) + ' ' + start.strftime('%Y')
        elif selection == 'year':
            year = int(self.year_select.year.data)
            start = date(year, 1, 1)
            end = date(year, 1, 1) + relativedelta(years=1, days=-1)
            period_label = 'Year {}'.format(start.strftime('%Y'))
        elif selection == 'custom':
            start, end = self.custom_date_select.custom_dates.data.split(" - ")
            start = datetime.strptime(start, "%m/%d/%Y")
            end = datetime.strptime(end, "%m/%d/%Y")
            period_label = '{} through {}'.format(start.strftime("%-m/%d/%Y"), end.strftime("%-m/%d/%Y"))
        return (start, end, period_label)


class ReportGiftCertForm(Form):
    FILTER_ALL = "all"
    FILTER_PURCHASED = "purchased"
    FILTER_MAKEUP = "makeup"
    FILTER_OTHER = "other"

    FILTER_CHOICES = (
        (FILTER_ALL, "All"),
        (FILTER_PURCHASED, "Purchased Only"),
        (FILTER_MAKEUP, "Makeup Only"),
        (FILTER_OTHER, "Paid with"),
    )
    studio = QuerySelectField(
        "Studio", widget=ChosenSelectWidget(), get_label="name",
        allow_blank=True, blank_text="All studios")
    filter = RadioField("Filter by purchase type", [validators.required()],
                        choices=FILTER_CHOICES)
    paid_with = SelectField("Paid with", choices=PAID_WITH_CATEGORIES)
    date = FormField(ReportDateForm)


class PlainReportForm(Form):
    studio = QuerySelectField(
        "Studio", widget=ChosenSelectWidget(), get_label="name",
        allow_blank=True, blank_text="All studios")
    date = FormField(ReportDateForm)


class MultipleStudioReportForm(Form):
    studio = QuerySelectMultipleField(
        "Studios", widget=ChosenSelectWidget(multiple=True), get_label="name",
        allow_blank=True, blank_text="All studios")
    date = FormField(ReportDateForm)

class NewsletterSubscribersReportForm(Form):
    SUBSCRIBE_REASON_CHOICES = (
        ("newsletter_signup","Signed up for newsletter"),
        ("class_signup","Signed up for class"),
        ("created_login","Created a login"),
        ("bought_gc","Bought a gift certificate"),
        ("received_gc","Received a gift certificate"),
        ("contact_page_email","Emailed from contact page"),
        ("admin_registered","Registered by admin"),
    )
    studio = QuerySelectField("Studio", [validators.required()],
        widget=ChosenSelectWidget(),
        query_factory=lambda: models.Studio.query,
        allow_blank=True, blank_text="All studios",
       get_label="name")
    reasons = SelectMultipleField("Subscribe Reason",
        widget=ChosenSelectWidget(multiple=True), choices=SUBSCRIBE_REASON_CHOICES)
    date = FormField(ReportDateForm)

class ClassesTaughtReportForm(Form):
    cls = QuerySelectField("Class", [validators.required()],
                           widget=ChosenSelectWidget(),
                           query_factory=lambda: models.Class.query,
                           allow_blank=True, blank_text="Select a class",
                           get_label="abbr")
    studio = QuerySelectMultipleField(
        "Studios", widget=ChosenSelectWidget(multiple=True), get_label="name",
        allow_blank=True, blank_text="All studios")
    date = FormField(ReportDateForm)


class SchedulePageReportForm(Form):
    teacher = QuerySelectField(
        "Teachers", [validators.required()], widget=ChosenSelectWidget(),
        query_factory=lambda: models.Teacher.query.join(models.User),
        blank_text="Select a teacher",
        get_label=lambda t: t.user.first_name)
    studio = QuerySelectMultipleField(
        "Studios", widget=ChosenSelectWidget(multiple=True), get_label="name",
        allow_blank=True, blank_text="All studios")
    date = FormField(ReportDateForm)


class SalesReportForm(Form):

    @staticmethod
    def item_choices():
        item_names = db.session.query(models.Product.name).distinct()
        return [('', '')] + sorted([(x[0], x[0]) for x in item_names])

    def __init__(self, *args, **kwargs):
        super(SalesReportForm, self).__init__(*args, **kwargs)
        self.item.choices = self.item_choices()

    teacher = QuerySelectField(
        "Teachers", widget=ChosenSelectWidget(),
        query_factory=lambda: models.Teacher.query.join(models.User),
        allow_blank=True, blank_text="All",
        get_label=lambda t: t.user.first_name)
    studio = QuerySelectField(
        "Studio", widget=ChosenSelectWidget(), get_label="name",
        allow_blank=True, blank_text="All studios")
    #method_of_payment = SelectField(
    #    "Method of payment", choices=models.ProductOrder.PAID_WITH_CHOICES)
    item = SelectField("Item", widget=ChosenSelectWidget())
    date = FormField(ReportDateForm)


class SalesOfTheDayReportForm(Form):
    ALL_SALES = ""
    ONLINE_SALES = "online"

    @staticmethod
    def teacher_choices():
        yield ("", "All")
        yield ("online", "Online Sales")
        teachers = db.session.query(
                models.Teacher.user_id,
                models.User.first_name
            )\
            .select_from(models.Teacher)\
            .join(models.User)
        for (username, teacher_id) in teachers:
            yield unicode(username), teacher_id

    teacher = SelectField("Sold by", widget=ChosenSelectWidget())
    studio = QuerySelectField(
        "Studio", widget=ChosenSelectWidget(), get_label="name",
        allow_blank=True, blank_text="All studios")
    date = FormField(ReportDateForm)

    def __init__(self, *args, **kwargs):
        super(SalesOfTheDayReportForm, self).__init__(*args, **kwargs)
        self.teacher.choices = self.teacher_choices()


class InventoryAdjustmentsReportForm(Form):
    product = QuerySelectField(
        "Product", widget=ChosenSelectWidget(), get_label="name",
        allow_blank=True, blank_text="All products", query_factory=lambda: models.Product.query)
    reason = RadioField("Reason", [validators.optional()], choices=models.ProductInventoryItem.REASONS)
    studio = QuerySelectField(
        "Studio", widget=ChosenSelectWidget(), get_label="name",
        allow_blank=True, blank_text="All studios")
    date = FormField(ReportDateForm)


class ProductInventoryAdjustForm(Form):

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.pi = kwargs.get('pi')

    def validate(self):
        no_errors = True
        rv = Form.validate(self)
        if not rv:
            no_errors = False
        if self.quantity.data and not self.reason.data:
            self.reason.errors.append("If you adjust the inventory, you must provide a reason.")
            no_errors = False
        if self.active.data == self.pi.active and (not self.quantity.data or not self.reason.data):
            self.quantity.errors.append("If not toggling an item's active state, you must enter a value in the Adjust Inventory field and give a reason.")
            no_errors = False
        if self.quantity.data and (self.pi.quantity_stocked + self.quantity.data) < 0:
            self.quantity.errors.append("Quantity removed is greater than that in stock.")
            no_errors = False
        if self.reason.data == "1" and not self.dest_campus.data:  # transferring to another campus
            self.dest_campus.errors.append("No campus specified.")
            no_errors = False
        if self.reason.data == "1" and self.quantity.data > -1:  # transferring to another campus
            self.quantity.errors.append("The amount to adjust must be negative for transfer to another campus.")
            no_errors = False
        if self.reason.data == "4" and not self.quantity.data > -1:  # transferring to another campus
            self.quantity.errors.append("The amount to adjust must be negative when pulling for studio use.")
            no_errors = False
        return no_errors

    quantity_to_stock = IntegerField()
    quantity = IntegerField("Adjust Inventory")
    date = DateField(format="%m/%d/%Y")
    reason = RadioField("Reason", [validators.required()], choices=models.ProductInventoryItem.REASONS)
    dest_campus = QuerySelectField(
        "Studio",
        widget=ChosenSelectWidget(),
        get_label="name",
        allow_blank=True,
        blank_text="",
        query_factory=lambda: models.Campus.query,
    )
    active = BooleanField()


class NewProductInventoryForm(Form):

    def validate(self):
        no_errors = True
        rv = Form.validate(self)
        if not rv:
            no_errors = False
        if not self.quantity_to_stock.data >= 0:
            self.quantity_to_stock.errors.append("You cannot have negative inventory.")
            no_errors = False
        return no_errors
    campus = QuerySelectField(
        "Studio",
        widget=ChosenSelectWidget(),
        get_label="name",
        blank_text="",
        query_factory=lambda: models.Campus.query,
    )
    product = QuerySelectField(
        widget=ChosenSelectWidget(),
        get_label="name",
        blank_text="",
        query_factory=lambda: models.Product.query,
    )
    quantity_to_stock = IntegerField()
    active = BooleanField()


class ScheduleOrderForm(Form):

    def validate(self):
        no_errors = True
        rv = Form.validate(self)
        if not rv:
            no_errors = False
        if self.paid.data < 0:
            self.paid.errors.append("You cannot have a negative amount paid.")
            no_errors = False
        if not self.paid_with.data == 'Freebie' and self.paid.data == 0:
            self.paid.errors.append("The amount paid must be greater than zero.")
            no_errors = False
        return no_errors

    first_name = TextField("First Name", [validators.required()])
    last_name = TextField("Last Name", [validators.required()])
    email = TextField("Email", [validators.required()])
    phone = TextField("Phone", [validators.required()])
    guest_count = IntegerField("Guests")
    comments = TextAreaField("Comments")
    #unit_price = DecimalField("Unit Price")
    paid_with = SelectField("Paid With", [validators.required()], choices=models.ScheduleOrder.PAID_WITH_CHOICES)
    paid = DecimalField("Amount Paid")
    cancelled = BooleanField("Cancelled", default=False)


class ShopOrderForm(Form):
    SHIPPING_CHOICES = (
        ("", "----------"),
        ("USPS", "USPS"),
        ("UPS", "UPS"),
        ("Store", "In-Store"),
    )

    studio = QuerySelectField(
        "Studio", widget=ChosenSelectWidget(), get_label="name")
    sold_by = QuerySelectField(
        "Sold by", allow_blank=True, blank_text="Online sale",
        widget=ChosenSelectWidget(), get_label=lambda t: t.user.first_name)
    online_sale = BooleanField("Online sale")
    in_store_pickup = BooleanField("In-store pickup")
    discount = IntegerField("Discount")
    paid_with = SelectField("Paid with", choices=models.ProductOrder.PAID_WITH_CHOICES)
    date_ordered = DateField("Date ordered", format="%m/%d/%Y", widget=DatePickerWidget())
    date_sent = DateField("Date sent", format="%m/%d/%Y", widget=DatePickerWidget())
    shipped_by = SelectField("Shipped by", choices=SHIPPING_CHOICES)
    sender_name = TextField("Sender name")
    sender_email = TextField("Sender email")
    sender_phone = TextField("Sender phone")
    street_address = TextField("Street address")
    city = TextField("City")
    state = TextField("State")
    zip_code = TextField("Zip code")

    @classmethod
    def new(cls, campus_ids, *args, **kwargs):
        shop_order_form = cls(*args, **kwargs)
        shop_order_form.studio.query = models.Campus.query\
            .filter(models.Campus.id.in_(campus_ids))
        shop_order_form.sold_by.query = models.Teacher.query\
            .distinct()

        if not kwargs["user"].is_superuser:
            shop_order_form.paid_with.choices = models.ProductOrder.PAID_WITH_CHOICES[0:4]

        return shop_order_form


class PhotoAlbumEditForm(Form):
    campus = QuerySelectField(
        "Studio", [], widget=ChosenSelectWidget(),
        query_factory=lambda: models.Campus.query, allow_blank=True,
        blank_text="Select a studio", get_label="name")
    name = TextField("Name", [validators.required()])
    #active = BooleanField("Is Active", default=True)


class StoreProductForm(Form):
    selected_product_id = IntegerField([validators.required()])
    quantity = IntegerField([validators.required()])

    def validate_with_quantity(self, count):
        return self.validate_on_submit() and self.quantity.data <= count
