from sqlalchemy import Column, and_, or_, Table, func, text, literal
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.types import (Text, String, Integer, DateTime, Time, Float,
                              Date, Boolean, Numeric, CHAR, Enum)
from sqlalchemy.schema import ForeignKey, Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.session import make_transient
from fractions import Fraction
from base64 import b32encode
from collections import OrderedDict
import hashlib, random
import logging
import re
from lxml import html, etree
from os import urandom
from collections import Counter
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from itertools import chain
from flask import Markup, render_template_string
from jinja2 import evalcontextfunction
from jinja2.utils import generate_lorem_ipsum
from pytz import timezone

from hipcooks import app, db, settings, utils, mail


class PermissionType(db.Model):
    __tablename__ = "permission_type"

    id = Column(Integer, primary_key=True)
    key = Column(String(30), index=True)
    name = Column(String(255))


class Permission(db.Model):
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    campus_id = Column(Integer, ForeignKey("Class_campus.campus_id"))
    permission_type_id = Column(Integer, ForeignKey("permission_type.id"))
    can_view = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)

    permission_type=relationship(PermissionType)


class Class(db.Model):
    __tablename__ = "Class_description"

    KNIFE_LEVELS = OrderedDict((str(i), v) for i, v in enumerate((
        "Learn great knife skills!",
        "Basic knife skills taught",
        "No knifing",
        "N/A",
    )))

    VEGGIE_LEVELS = OrderedDict((str(i), v) for i, v in enumerate((
        "Vegetarian",
        "Vegetarians welcome with advance notice",
        "Pescatarian, vegetarians welcome with advance notice",
        "Pescatarian",
        "Meat-eater's class! Vegetarians welcome with advance notice",
        "Meat-eater's class! Pescatarians welcome with advance notice",
        "Meat-eater's class!",
        "N/A",
    )))

    DAIRY_LEVELS = OrderedDict((str(i), v) for i, v in enumerate((
        "Dairy-free",
        "Dairy-free welcome with advance notice",
        "Not dairy-free",
        "N/A",
    )))

    WHEAT_LEVELS = OrderedDict((str(i), v) for i, v in enumerate((
        "Wheat-free",
        "Wheat-free welcome with advance notice",
        "Not wheat-free",
        "N/A",
    )))

    BASIC_CATEGORIES = (("knife skills", "knife skills"),
                        ("vegetarian", "vegetarian"),
                        ("dairy-free", "dairy-free"),
                        ("wheat-free", "wheat-free"))

    id = Column("description_id", Integer, primary_key=True)
    order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    abbr = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    menu = Column(Text, nullable=False)
    wine = Column(String(255), nullable=False)
    knife_level = Column(String(1), nullable=False)
    veggie_level = Column(String(1), nullable=False)
    dairy_level = Column(String(1), nullable=False)
    wheat_level = Column(String(1), nullable=False)
    cost_override = Column(Integer, nullable=True, default=None)
    color_code = Column(String(7))

    @property
    def admin_name(self):
        return Markup('<span title="{}">{}</span>').format(
            self.title, self.abbr)

    @property
    def knife(self):
        return Class.KNIFE_LEVELS.get(self.knife_level, "N/A")

    @property
    def veggie(self):
        return Class.VEGGIE_LEVELS.get(self.veggie_level, "N/A")

    @property
    def dairy(self):
        return Class.DAIRY_LEVELS.get(self.dairy_level, "N/A")

    @property
    def wheat(self):
        return Class.WHEAT_LEVELS.get(self.wheat_level, "N/A")

    def new_schedule(self):
        return Schedule(cls=self, is_public=True)

    @property
    def photos(self):
        return self.photos_query.order_by(ClassPhoto.order.asc())


class Campus(db.Model):
    __tablename__ = "Class_campus"

    id = Column("campus_id", Integer, primary_key=True)
    domain = Column(String(31))
    name = Column(String(255))
    abbreviation = Column(String(6))
    tab_name = Column(String(255))
    order = Column(Integer)
    class_size = Column(Integer)
    start_time = Column(Time)
    duration = Column(Integer)
    base_cost = Column(Integer)
    private_class_fee = Column(Integer)
    email = Column(String(75))
    phone = Column(String(20))
    address = Column(String(255))
    directions = Column(Text)
    embed_url = Column(Text)
    city = Column(String(50))
    state = Column(String(2))
    zipcode = Column(String(10))
    sales_tax = Column(Numeric(4,2))
    authorize_net_login = Column(String(12))
    authorize_net_tran_key = Column(String(16))
    facebook_url = Column(String(100))
    instagram_url = Column(String(100))
    google_plus_url = Column(String(100))
    yelp_url = Column(String(100))
    color_code = Column(String(7))
    class_in_session_body = Column(Text)
    the_skinny_body = Column(Text)
    private_class_page_text = Column(Text)
    private_class_page_policy_text = Column(Text)

    def __str__(self):
        return self.name

    @classmethod
    def ordered_query(cls):
        return db.session.query(cls).order_by(cls.order.asc())

    @property
    def photo_route(self):
        return utils.url_path(self.photo_directory, self.photo_filename)

    @property
    def photo_filename(self):
        return str(self.domain) + '_studio_photo'

    photo_directory = "studio-photos"


class PhotoAlbum(db.Model):
    __tablename__ = "Class_album"

    id = Column("album_id", Integer, primary_key=True)
    name = Column(String(30))
    active = Column(Boolean, default=True)
    campus_id = Column(Integer, ForeignKey(Campus.id), nullable=True)

    campus = relationship(Campus)


class ClassPhoto(db.Model):
    __tablename__ = "Class_photo"

    id = Column("photo_id", Integer, primary_key=True)
    caption = Column(String(255))
    photo = Column(String(100))
    order = Column(Integer)
    class_id = Column("for_class_id", Integer, ForeignKey(Class.id),
                      nullable=True)
    album_id = Column("album_id", Integer, ForeignKey(PhotoAlbum.id), nullable=True)
    home_page = Column(Boolean, default=True)

    cls = relationship(Class, backref=backref("photos_query", lazy="dynamic"))
    album = relationship(PhotoAlbum, backref=backref("photos", lazy="dynamic"))

    @property
    def url(self):
        return utils.url_path("class_images", self.photo)


class RecipeSet(db.Model):
    id = Column(Integer, ForeignKey(Class.id), primary_key=True)
    intro = Column(Text)
    menu = Column(Text)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)

    cls = relationship(Class, backref=backref("recipe_set", lazy="dynamic"))

    @property
    def ordered_recipes(self):
        return self.recipes.order_by(Recipe.order.asc()).all()


class Recipe(db.Model):
    id = Column("recipe_id", Integer, primary_key=True)
    set_id = Column(Integer, ForeignKey(RecipeSet.id))
    intro = Column(Text)
    title = Column(String(100))
    serves = Column(String(100))
    ingredients = Column(Text)
    instructions = Column(Text)
    order = Column(Integer)

    set = relationship(
        RecipeSet, backref=backref("recipes", lazy="dynamic"))


class Setup(db.Model):
    id = Column(Integer, ForeignKey(Class.id), primary_key=True)
    pre_prep = Column(Text)
    prep = Column(Text)
    setup = Column(Text)
    class_intro = Column(Text)
    menu_intro = Column(Text)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)

    cls = relationship(Class)

    def clean_text(self):
        for attr in ["pre_prep", "prep", "setup", "class_intro", "menu_intro" ]:
            setattr(self, attr, self._fix_html(getattr(self, attr)))
        for rnd in self.rounds:
            rnd.round_intro = self._fix_html(rnd.round_intro)
            for pnt in rnd.points:
                pnt.action_point = self._fix_html(pnt.action_point)
                pnt.teaching_point = self._fix_html(pnt.teaching_point)

    def _coerce_sentences(self, text):
        words = text.split(" ")
        new_words = []
        last_word = None
        for word in words:
            if not last_word or re.search(r"[\.?:!]$", last_word):
                word = word.title()
            else:
                word = word.lower()

            last_word = word
            new_words.append(word)

        text = " ".join(new_words)
        if not re.search(r"[\.?:!]$", text):
            text = text + "."

        return text

    def _recursive_fix(self, el):
        if el.text:
            el.text = self._coerce_sentences(el.text)
        for child in el:
            self._recursive_fix(child)

    def _fix_html(self, item):
        if not item:
            return item
        tree = html.fromstring(item.replace("\r", ""))
        self._recursive_fix(tree)

        return etree.tostring(tree)


class SetupRound(db.Model):
    id = Column(Integer, primary_key=True)
    setup_id = Column(Integer, ForeignKey(Setup.id))
    round_number = Column(Integer)
    round_intro = Column(Text)

    setup = relationship(
        Setup, backref=backref("rounds", cascade="all, delete-orphan"))


class SetupRoundPoint(db.Model):
    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey(SetupRound.id))
    teaching_point = Column(Text)
    action_point = Column(Text)

    round = relationship(
        SetupRound, backref=backref("points", cascade="all, delete-orphan"))


class ShoppingList(db.Model):
    id = Column(Integer, ForeignKey(Class.id), primary_key=True)
    check = Column(Text)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)

    cls = relationship(Class, backref=backref("shopping_list"))

    @property
    def category_ordered_items(self):
        return db.session.query(ShoppingListItem)\
                    .filter(ShoppingListItem.shopping_list == self)\
                    .filter(ShoppingListItem.active == True)\
                    .order_by(ShoppingListItem.category,ShoppingListItem.name)\
                    .all()


class MixedNumberItem(object):
    @property
    def hash(self):
        return u"{}{}".format(self.name.strip().rstrip().rstrip("esi"), self.market.lower())

    @property
    def sli_hash(self):
        return u"{}{}{}".format(self.name.strip().rstrip().rstrip("esi"), self.market.lower(), self.shopping_list.id)

    @property
    def mixed_number(self):
        mixed = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$", self.number)
        fract = re.match(r"^(\d+)\s*/\s*(\d+)$", self.number)
        if mixed or fract:
            if mixed:
                return int(mixed.group(1)) + Fraction("{}/{}".format(mixed.group(2), mixed.group(3)))
            else:
                return Fraction("{}/{}".format(fract.group(1), fract.group(2)))
        elif re.match(r"^\d*\.\d+$", self.number):
            return float(self.number)
        else:
            try:
                return int(self.number)
            except ValueError:
                return 1


class ShoppingListItem(db.Model, MixedNumberItem):
    CATEGORIES = {
        "dairy": "Dairy",
        "drink": "Drink",
        "drygoods": "Dry Goods",
        "meat": "Fish/Meat/Poultry",
        "frozen": "Frozen",
        "produce": "Produce",
        "check": "Check"
    }

    id = Column(Integer, primary_key=True)
    category = Column(String(10), nullable=False)
    shopping_list_id = Column(Integer, ForeignKey(ShoppingList.id))
    number = Column(String(5))
    unit = Column(String(25))
    name = Column(String(255))
    market = Column(String(255), nullable=False)
    notes = Column(String(255), nullable=False)
    active = Column(Boolean(), default=True)

    shopping_list = relationship(
        ShoppingList, backref=backref("items", lazy="dynamic")
    )

    @property
    def original_items(self):
        return []

    @property
    def campus(self):
        return ""


class ClassInstance(db.Model):
    __tablename__ = "classes"

    id = Column("class_id", Integer, primary_key=True)
    class_id = Column("desc_id", Integer,
                      ForeignKey(Class.id))
    date = Column(Date)
    time = Column(String(20))
    campus_id = Column(Integer, ForeignKey("Class_campus.campus_id"))


class User(db.Model):
    __tablename__ = "auth_user"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50), nullable=False, server_default="")
    email = Column(String(75))
    password = Column(String(128))
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created = Column("date_joined", DateTime(timezone=True), default=datetime.utcnow)

    def __str__(self):
        return u"{} {}".format(self.first_name, self.last_name)

    def is_duplicate_with(self, *names):
        or_clause = or_(*chain(*((User.email == name, User.username == name)
                        for name in names)))
        return db.session.query(User)\
            .filter(or_clause, User.id != self.id)\
            .count() > 0

    @staticmethod
    def find_user(id=None, email=None):
        if id is not None:
            user = db.session.query(User).get(id)
            if user is not None:
                return user
        if email is not None:
            user = db.session.query(User).filter_by(email=email).first()
            if user is not None:
                return user
        return User()

    @classmethod
    def hash_password(cls, password):
        salt = hashlib.sha1(str(random.random())).hexdigest()[0:4]
        return ("sha1$" + salt + "$" +
                hashlib.sha1(salt + password).hexdigest())

    def set_password(self, password):
        self.password = self.hash_password(password)

    def valid_password(self, password):
        algo, salt, hsh = self.password.split("$")
        return hashlib.sha1(salt + password).hexdigest() == hsh

    def can_view(self, permission, campus_id = None):
        if self.is_superuser:
            return True
        perm = db.session.query(Permission).select_from(PermissionType)\
                                            .join(Permission)\
                                            .filter(
                                                Permission.user_id == self.id,
                                                PermissionType.key == permission,
                                                Permission.can_view == True
                                            )

        if campus_id:
            perm = perm.filter(Permission.campus_id == campus_id)

        return perm.count() > 0

    def can_update(self, permission, campus_id = None):
        if self.is_superuser:
            return True
        perm = db.session.query(Permission).select_from(PermissionType)\
                                            .join(Permission)\
                                            .filter(
                                                Permission.user_id == self.id,
                                                PermissionType.key == permission,
                                                Permission.can_update == True
                                            )
        if campus_id:
            perm = perm.filter(Permission.campus_id == campus_id)

        return perm.count() > 0


class TeacherCampus(db.Model):
    __tablename__ = "Class_teacher_campuses"
    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("Class_teacher.user_id"))
    campus_id = Column(Integer, ForeignKey("Class_campus.campus_id"))
    role_name = Column(String(30), nullable=True)


class UserNotes(db.Model):
    __tablename__ = "auth_user_notes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    notes = Column(Text)

    user = relationship(User, backref=backref("notes", uselist=False))


class Teacher(db.Model):
    __tablename__ = "Class_teacher"

    user_id = Column(Integer, ForeignKey("auth_user.id"), primary_key=True)
    bio = Column(Text)
    pic = Column(String(100), nullable=True)
    mobile_phone = Column(String(20))
    street = Column(String(255))
    city = Column(String(255))
    state = Column(String(2))
    zip_code = Column(String(10))
    ssn = Column(String(11))
    active = Column(Boolean, default=True)

    campuses = relationship(Campus, secondary="Class_teacher_campuses", backref="teachers")
    user = relationship(User)

    PICTURE_DIR = "profile-pics"

    def __str__(self):
        return self.user.first_name

    @property
    def pic_url(self):
        if self.pic is None:
            return ""
        return utils.url_path(self.PICTURE_DIR, self.pic)

    @property
    def default_filename(self):
        return "{}_pic".format(self.user_id)

    @staticmethod
    def get_monika():
        if hasattr(settings, 'MONIKA_ID'):
            monika = db.session.query(Teacher).get(settings.MONIKA_ID)
        else:
            monika = db.session.query(Teacher).join(User)\
                                              .filter(User.first_name == 'Monika', User.last_name == 'Reti')\
                                              .one()
        return monika

    @staticmethod
    def get_kyrsten():
        if hasattr(settings, 'KYRSTEN_ID'):
            kyrsten = db.session.query(Teacher).get(settings.KYRSTEN_ID)
        else:
            kyrsten = db.session.query(Teacher).join(User)\
                                               .filter(User.first_name == 'Kyrsten', User.last_name == 'Beidelman')\
                                               .one()
        return kyrsten

    def is_duplicate_with(self, *names):
        or_clause = or_(*chain(*((User.email == name, User.username == name)
                        for name in names)))
        return db.session.query(Teacher)\
            .join(User)\
            .filter(or_clause, User.id != self.user_id)\
            .count() > 0

assistant_campuses = Table("Class_assistant_campuses", db.Model.metadata,
                        Column("assistant_id", Integer, ForeignKey("Class_assistant.assistant_id")),
                        Column("campus_id", Integer, ForeignKey("Class_campus.campus_id"))
                    )


class Assistant(db.Model):
    __tablename__ = "Class_assistant"

    id = Column("assistant_id", Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    first_name = Column(String(255))
    last_name = Column(String(255))
    active = Column(Boolean, default=True)
    email = Column(String(75))
    mobile_phone = Column(String(20))
    classes = Column(Integer, default=0)
    credits = Column(Integer, default=0)

    campuses = relationship(Campus, secondary=assistant_campuses, backref="assistants")
    user = relationship(User)

    @staticmethod
    def query_active():
        return db.session.query(Assistant).filter_by(active=True).order_by(Assistant.first_name)

    @property
    def schedule_undeleted_classes(self):
        return [x for x in self.schedule_classes if x.deleted is not True]

    def is_duplicate_with(self, *names):
        or_clause = or_(*chain(*((User.email == name, User.username == name)
                        for name in names)))
        return db.session.query(Assistant)\
            .join(User)\
            .filter(or_clause, User.id != self.user_id)\
            .count() > 0

    # TODO: I can't see how they associated gift certs with assistants. I can only conclude that
    # they used email...but that's awful of course. :\ We should change this and migrate...for now
    # I'll leave it like it is till I get better info.
    @property
    def gift_certificate_credits(self):
        try:
            c = int(db.session.query(func.sum(GiftCertificate.amount_to_give))\
                    .select_from(GiftCertificate)\
                    .filter(GiftCertificate.sender_email==self.user.email, GiftCertificate.paid_with=='Assistant')\
                    .scalar()) / 65
        except TypeError:
            return 0

        return c

    @property
    def full_name(self):
        return unicode(self).strip()

    def __unicode__(self):
        return u"{} {}".format(self.user.first_name, self.user.last_name)

schedule_teachers = Table(
    "Class_schedule_teachers", db.Model.metadata,
    Column("schedule_id", Integer, ForeignKey("Class_schedule.schedule_id")),
    Column("teacher_id", Integer, ForeignKey("Class_teacher.user_id")),
)

schedule_assistants = Table(
    "Class_schedule_assistants", db.Model.metadata,
    Column("schedule_id", Integer, ForeignKey("Class_schedule.schedule_id")),
    Column("assistant_id", Integer,
           ForeignKey("Class_assistant.assistant_id")),
)


class PrePrepList(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    created = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    active = Column(Boolean, default=True)
    name = Column(String(255))

    @staticmethod
    def create_list_instance(user_id, name, classes):
        db.session.begin()
        list_instance = PrePrepList(
            user_id=user_id,
            name=name
        )
        db.session.add(list_instance)

        for class_id in classes:
            list_instance.add_item(class_id)

        db.session.commit()
        return list_instance

    def add_item(self, class_id):
        # If the user enters a fraction, try to be slick and add correctly. This might be total overkill.
        setup = db.session.query(Setup).get(class_id)
        item = PrePrepListItem(
            text=setup.pre_prep,
            setup_id=setup.id,
        )
        self.items.append(item)


class PrePrepListItem(db.Model):
    id = Column(Integer, primary_key=True)
    pre_prep_list_id = Column(Integer, ForeignKey(PrePrepList.id))
    setup_id = Column(Integer, ForeignKey(Setup.id))
    text = Column(Text)

    pre_prep_list = relationship(
        PrePrepList, backref=backref("items", cascade="all,delete"), cascade="all,delete")

    setup = relationship(Setup)


class Schedule(db.Model):
    __tablename__ = "Class_schedule"

    id = Column("schedule_id", Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id))
    class_id = Column("description_id", Integer, ForeignKey(Class.id))
    is_public = Column(Boolean, server_default='1')
    date = Column(Date)
    time = Column(Time)
    duration = Column(Float)
    spaces = Column(Integer)  # smallint(5) unsigned
    comments = Column(String(255), nullable=True)
    sent_reminder = Column(Boolean, server_default='0')
    sent_recipe = Column(Boolean, server_default='0')
    is_an_event = Column(Boolean, server_default='0')
    deleted = Column(Boolean, default=False)

    # Fields for private classes and events
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(75), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    company_name = Column(String(255), nullable=True)
    event_reason = Column(String(255), nullable=True)

    campus = relationship(Campus)
    cls = relationship(Class)
    teachers = relationship(Teacher, secondary=schedule_teachers)
    assistants = relationship(Assistant, secondary=schedule_assistants, backref="schedule_classes")

    @property
    def formatted_date(self):
        return self.date.strftime('%a, %b %d')

    @property
    def formatted_date_year(self):
        return self.date.strftime('%b %d, %Y')

    @property
    def formatted_time(self):
        return self.time.strftime("%-I:%M %p")

    @property
    def color(self):
        return self.campus.color_code

    @property
    def class_color(self):
        return self.cls.color_code

    @property
    def time_range(self):
        delta = timedelta(hours=int(self.duration),
                          minutes=int((self.duration % 1) * 60))
        start = datetime.combine(self.date, self.time)
        end = start + delta
        return utils.format_time_range(start.time(), end.time())

    def floored_remaining_spaces(self, floor_value=False):
        spaces = self.remaining_spaces()
        if spaces > 0:
            return spaces
        else:
            return floor_value

    def remaining_spaces(self):
        return self.spaces - sum(
            order.active_members for order in self.orders)

    @property
    def cost(self):
        if self.cls.cost_override is not None:
            return self.cls.cost_override
        else:
            return self.campus.base_cost

    @property
    def start_time(self):
        start_time = datetime.combine(self.date, self.time)
        return start_time

    @property
    def end_time(self):
        delta = timedelta(hours=int(self.duration),
                          minutes=int((self.duration % 1) * 60))
        start_time = datetime.combine(self.date, self.time)
        end_time = start_time + delta
        return end_time

    @property
    def no_shows(self):
        return [order.user for order in self.orders.filter(ScheduleOrder.no_show == True)]

    @property
    def extra_students(self):
        return self.extra_people.filter(ExtraPerson.order_id == None)

    @property
    def substitutes(self):
        return self.extra_people.filter(ExtraPerson.order_id != None)

    @property
    def total_attendees(self):
        return self.orders.filter(ScheduleOrder.no_show == False).count() + self.extra_students.count()


class Purchase(db.Model):
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address = Column(CHAR(15))
    amount = Column(Integer)
    first_name = Column(String(255))
    last_name = Column(String(255))
    address1 = Column(String(255), nullable=True)
    address2 = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(CHAR(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    country = Column(CHAR(2), nullable=True)
    email = Column(String(75))
    phone = Column(String(20), nullable=True)
    authorization_code = Column(CHAR(6))
    user_id = Column(Integer, ForeignKey(User.id))

    user = relationship(User, backref="purchases")


class ScheduleOrder(db.Model):
    PAID_WITH_CHOICES = (
        ("", "--None--"),
        ("CC", "CC", ),
        ("GC", "GC",),
        ("CC + GC", "CC + GC",),
        ("Call-in CC", "Call-in CC",),
        ("Freebie", "Freebie",),
        ("Assistant", "Assistant",),
        ("Donation", "Donation",),
        ("Check", "Check",),
        ("Cash", "Cash",),
        ("Makeup", "Makeup",),
        ("CC+Makeup", "CC+Makeup",),
    )

    id = Column("order_id", Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey(Schedule.id))
    user_id = Column(Integer, ForeignKey(User.id))
    first_name = Column(String(255))
    last_name = Column(String(255))
    active = Column(Boolean, default=True, nullable=False, server_default='1')
    email = Column(String(75))
    phone = Column(String(20))
    purchase_id = Column(Integer, ForeignKey("purchase.id"), nullable=True)
    comments = Column(String(255), default="")
    unit_price = Column(Integer)
    cancelled = Column(Boolean, default=False)
    datetime_cancelled = Column(DateTime(timezone=True), default=datetime.utcnow)
    no_show = Column(Boolean, default=False)
    paid_with = Column(String(10))
    paid = Column(Float)
    interested_in_assisting = Column(Boolean, default=False)
    code = Column(String(10), index=True, unique=True, nullable=False, default=lambda: b32encode(urandom(5))[:7])
    created = Column(DateTime(timezone=True), default=datetime.utcnow)

    schedule = relationship(Schedule,
                            backref=backref("orders", lazy="dynamic"))
    user = relationship(User, backref=backref("orders", lazy="dynamic"))
    purchase = relationship(lambda: Purchase,
                        backref=backref("schedules", lazy="dynamic"))

    @property
    def in_past(self):
        now = datetime.utcnow()
        return datetime.combine(self.schedule.date, self.schedule.time) < now

    @property
    def past_cancellation_period(self):
        now = datetime.utcnow()
        cls_datetime = datetime.combine(self.schedule.date, self.schedule.time)
        return now > (cls_datetime + relativedelta(days=-2))

    @property
    def total_cost(self):
        return self.unit_price * self.active_members

    @property
    def active_members(self):
        return len(self.active_guests) + (0 if self.cancelled else 1)

    @property
    def active_guests(self):
        return [g for g in self.guests if not g.cancelled]

    @property
    def active_emails(self):
        return [self.email] + filter(None, [x.email for x in self.active_guests])

    @property
    def gift_certificates_used(self):
        return db.session.query(GiftCertificate).join(GiftCertificateUse)\
                    .filter(GiftCertificateUse.purchase == self.purchase)\
                    .all()

    @property
    def gift_certificate_paid(self):
        gc_uses = db.session.query(GiftCertificateUse)\
                            .filter(GiftCertificateUse.purchase == self.purchase)\
                            .all()
        return sum(filter(None, [x.amount for x in gc_uses]))

class GuestOrder(db.Model):
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey(ScheduleOrder.id))
    name = Column(String(255), nullable=False, default="")
    email = Column(String(75), default="")
    cancelled = Column(Boolean, nullable=False, server_default=literal(False))

    order = relationship(
        ScheduleOrder, backref=backref("guests", cascade="all, delete-orphan"))


class OldScheduleOrder(db.Model):
    __tablename__ = "Shop_order"

    id = Column("order_id", Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey(Schedule.id))
    cancelled = Column(Boolean, default=False)


class OldGuestOrder(db.Model):
    __tablename__ = "Shop_guest"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey(OldScheduleOrder.id))
    cancelled = Column(Boolean)


class WaitingList(db.Model):
    __tablename__  = "Class_waitinglist"

    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey(Schedule.id))
    name = Column(String(255))
    email = Column(String(75))
    phone = Column(String(20))
    guests = Column(Integer)  # smallint(5) unsigned
    guest_information = Column(Text)
    tstamp = Column(DateTime(timezone=True), default=datetime.utcnow)

    schedule = relationship(Schedule, backref=backref("waitlists"))


class GiftCertificateBlock(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    campus_id = Column(Integer, ForeignKey(Campus.id))
    sender_name = Column(String(100))
    sender_email = Column(String(75))
    sender_phone = Column(String(20), nullable=True)
    amount_to_give = Column(Integer)  # smallint(5) unsigned
    recipient_name = Column(String(100))
    message = Column(Text)
    date_sent = Column(Date, nullable=True)
    paid_with = Column(String(10), nullable=True)
    expiration_date = Column(Date, nullable=True)
    total_certs = Column(Integer)
    created = Column("created", DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)

    campus = relationship(Campus)

    def generate_cert(self):
        gc = GiftCertificate(
            campus=self.campus,
            block=self,
            sender_name=self.sender_name,
            sender_email=self.sender_email,
            sender_phone=self.sender_phone,
            amount_to_give=self.amount_to_give,
            recipient_name=self.recipient_name,
            message=self.message,
            giftcard=False,
            date_sent=self.date_sent,
            paid_with=self.paid_with,
            expiration_date=self.expiration_date,
        )
        return gc


class GiftCertificate(db.Model):
    __tablename__  = "Shop_giftcertificate"

    DELIVER_EMAIL_ME = 1
    DELIVER_EMAIL_OTHER = 2
    DELIVER_MAIL = 3

    CATEGORY_CC = "CC"
    CATEGORY_CALL_IN = "Call-in CC"
    CATEGORY_FREEBIE = "Freebie"
    CATEGORY_ASSISTANT = "Assistant"
    CATEGORY_DONATION = "Donation"
    CATEGORY_CHECK = "Check"
    CATEGORY_CASH = "Cash"
    CATEGORY_MAKEUP = "Makeup Class"
    CATEGORY_PRIVATE = "Private"
    CATEGORY_GROUPON = "Groupon"

    CATEGORIES_PURCHASED = (
        CATEGORY_CC,
        CATEGORY_CALL_IN,
        CATEGORY_CHECK,
        CATEGORY_CASH,
        CATEGORY_PRIVATE,
    )

    id = Column("certificate_id", Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id))
    purchase_id = Column(Integer, ForeignKey("purchase.id"))
    delivery_method = Column(Integer)
    created = Column(DateTime(timezone=True), default=datetime.utcnow)
    sender_name = Column(String(100))
    sender_email = Column(String(75))
    sender_phone = Column(String(20), nullable=True)
    amount_to_give = Column(Integer)  # smallint(5) unsigned
    recipient_name = Column(String(100))
    recipient_email = Column(String(75), nullable=True)
    message = Column(Text)
    giftcard = Column(Boolean)
    date_sent = Column(Date, nullable=True)
    name_on_envelope = Column(String(255), nullable=True)
    street_address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    code = Column(
        String(10), nullable=True, default=lambda: b32encode(urandom(5))[:7])
    creditcard_id = Column(Integer, nullable=True)
    paid_with = Column(String(10), nullable=True)
    expiration_date = Column(Date, nullable=True)
    block_id = Column(Integer, ForeignKey(GiftCertificateBlock.id))

    campus = relationship(Campus)
    purchase = relationship(Purchase, backref="gift_certificates")
    block = relationship(GiftCertificateBlock, backref="gift_certificates")

    @staticmethod
    def new_for_purchase(order):
        gc = GiftCertificate(
            campus_id=order["campus_id"],
            delivery_method=order["delivery_method"],
            sender_name=order["sender_name"],
            sender_email=order["sender_email"],
            sender_phone=order["sender_phone"],
            amount_to_give=order["amount_to_give"],
            recipient_name=order["recipient_name"],
            recipient_email=order["recipient_email"],
            message=order["message"],
            giftcard=(int(order["delivery_method"]) ==
                      GiftCertificate.DELIVER_MAIL),
            name_on_envelope=order["name_on_envelope"],
            street_address=order["street_address"],
            city=order["city"],
            state=order["state"],
            zip_code=order["zip_code"],
        )
        return gc

    @staticmethod
    def outstanding_certs(recipient_email):
        return db.session.query(
                GiftCertificate,
                (GiftCertificate.amount_to_give - func.ifnull(
                    func.sum(GiftCertificateUse.amount),
                    0,
                )).label("remaining"),
            )\
            .outerjoin(GiftCertificateUse)\
            .filter(GiftCertificate.recipient_email == recipient_email)\
            .having(text("remaining > 0"))\
            .group_by(GiftCertificate.id)

    @staticmethod
    def total_amount(ids):
        amount = 0.0
        for gcid in ids:
            gc = db.session.query(GiftCertificate).get(gcid)
            uses = db.session.query(GiftCertificateUse).filter(GiftCertificateUse.certificate_id==gcid).all()
            used = sum(filter(None, [x.amount for x in uses]))
            amount += gc.amount_to_give - float(used)
        return amount

    @property
    def is_card(self):
        return self.giftcard

    @property
    def is_for_recipient(self):
        return self.delivery_method == self.DELIVER_EMAIL_OTHER

    @property
    def used_amount(self):
        return sum(use.amount for use in self.used_for)

    @property
    def amount_remaining(self):
        return max(self.amount_to_give - self.used_amount, 0)

    def adjust_assistant_credits(self, preexisting_amount, new_amount, cert_exists):
        if self.paid_with == 'Assistant':
            db.session.begin(subtransactions=True)
            assistant = db.session.query(Assistant).join(User).filter(User.email == self.sender_email).one()
            if cert_exists:
                preexisting_credits = int(preexisting_amount) / 65
                adjusted_credits = new_amount / 65
                new_credits = adjusted_credits - preexisting_credits
            else:
                new_credits = new_amount / 65
            assistant.credits += new_credits
            if assistant.credits < 0:
                assistant.credits = 0
            db.session.add(assistant)
            db.session.commit()


class GiftCertificateUse(db.Model):
    id = Column(Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id))
    certificate_id = Column(Integer, ForeignKey(GiftCertificate.id),
                            nullable=False)
    purchase_id = Column(Integer, ForeignKey(Purchase.id), nullable=True)
    amount = Column(Numeric(6, 2), nullable=False)
    date = Column(Date, nullable=False, default=date.today)

    campus = relationship(Campus)
    certificate = relationship(GiftCertificate, backref=backref("used_for"))
    purchase = relationship(Purchase)


class Product(db.Model):
    __tablename__ = "Shop_product"

    id = Column("product_id", Integer, primary_key=True)
    photo_id = Column(Integer, ForeignKey(ClassPhoto.id))
    name = Column(String(128))
    type = Column(String(128))
    price = Column(Numeric(6, 2))
    description = Column(Text)
    available_to_ship = Column(Boolean)
    cost_to_ship = Column(Numeric(5, 2))
    row = Column(Integer)
    column = Column(Integer)
    kitchen_row = Column(Integer)
    kitchen_column = Column(Integer)
    active = Column(Boolean, default=True)
    is_resource = Column(Boolean, nullable=False,
                         server_default=literal(False))
    splash_type = Column(Boolean, default=False)
    resource_name = Column(String(255))

    photo = relationship(ClassPhoto)

    image_dir = "product_images"

    @property
    def base_name(self):
        return hashlib.sha1(str(self.photo.id) + "product_images").hexdigest()

    @property
    def url(self):
        return utils.url_path(self.image_dir, self.base_name)

    @property
    def thumbnail_url(self):
        return utils.url_path('thumbnails', self.base_name)

    @property
    def description_or_default(self):
        if self.description:
            return self.description
        else:
            splash_product = Product.query\
                                    .filter(Product.name == self.name,
                                            Product.splash_type == True)\
                                    .first()
            if splash_product:
                return splash_product.description
            else:
                return self.description

    def remaining(self, campus_id):
        return int(ProductInventory.stocked(campus_id, self.id))

    def base_price(self, quantity):
        return self.price*quantity

    def shipping_price(self, quantity, pickup):
        if pickup:
            return 0
        else:
            return self.cost_to_ship * quantity

    def tax_price(self, quantity, sales_tax, discount=0):
        return self.price*quantity*(sales_tax/100)*(1 - Decimal(discount)/100)


class ProductInventory(db.Model):
    __tablename__ = "Shop_productinventory"

    id = Column(Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    quantity_to_stock = Column(Integer)  # int(10) unsigned
    quantity_stocked = Column(Integer)
    active = Column(Boolean)

    product = relationship(Product)
    campus = relationship(Campus)

    @staticmethod
    def stocked(campus_id, product_id):
        stocked = ProductInventory.query\
            .filter(ProductInventory.campus_id == campus_id, ProductInventory.product_id == product_id)\
            .filter(ProductInventory.active == True)\
            .first()
        if stocked is None:
            return 0
        return stocked.quantity_stocked if stocked.quantity_stocked is not None else 0


class ProductInventoryItem(db.Model):
    REASONS = (
        ("0", 'Received Shipment'),
        ("1", 'Transfer To'),
        ("2", 'Damaged or Broken'),
        ("3", 'Missing/Extra'),
        ("4", 'Pulled for Studio Use'),
    )
    __tablename__ = "Shop_productinventoryitem"

    id = Column(Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    date_stocked = Column(Date, default=date.today)
    quantity = Column(Integer)
    reason = Column(Integer)
    to_campus = Column(Integer, ForeignKey(Campus.id))
    blame = Column(Integer, ForeignKey(User.id))
    inventory_adjustment = Column(Boolean)

    product = relationship(Product, foreign_keys=[product_id])
    campus = relationship(Campus, foreign_keys=[campus_id])
    dest_campus = relationship(Campus, foreign_keys=[to_campus])

    @property
    def reason_str(self):
        try:
            reason = dict(ProductInventoryItem.REASONS)[str(self.reason)]
        except KeyError:
            return "Unknown"

        if self.reason == 1:
            return "{} {}".format(reason, "??" if self.dest_campus is None else self.dest_campus.name)
        return reason


class Transaction(db.Model):
    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey(Purchase.id), index=True)
    payment_method = Column(String(20))
    purchase_type = Column(String(20))
    amount = Column(Integer)
    card_number = Column(String(16), nullable=True)
    exp_month = Column(Integer, nullable=True)
    exp_year = Column(Integer, nullable=True)
    authorization_code = Column(String(6), nullable=True)
    remote_transaction_id = Column(String(20), nullable=True)

    purchase = relationship(Purchase, backref=backref("transactions"))


class StaticPage(db.Model):
    CATEGORY_CONTENT = "c"
    CATEGORY_EMAIL = "e"
    CATEGORY_PAGE = "p"
    CATEGORY_CHOICES = {"c": "Page Content", "p": "Page", "e": "Email"}

    id = Column(Integer, primary_key=True)
    path = Column(String(100), index=True, unique=True)
    title = Column(String(255))
    body = Column(Text)
    category = Column(String(1))
    description = Column(String(100))
    email_subject = Column(String(100))

    @property
    def full_category(self):
        return StaticPage.CATEGORY_CHOICES[self.category]

    @staticmethod
    def get_content(path):
        return StaticPage.query\
            .filter_by(path=path, category=StaticPage.CATEGORY_CONTENT)\
            .one()

app.template_global('get_content')(StaticPage.get_content)


@app.template_global('include_content')
@evalcontextfunction
def include_content(eval_ctx, page):
    try:
        return Markup(render_template_string(
            StaticPage.get_content(page).body, context=eval_ctx))
    except NoResultFound:
        logging.error("No content found with path: %s", page)
        return generate_lorem_ipsum()


class ShoppingListInstance(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(User.id))
    created = Column("created", DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    active = Column(Boolean, default=True)
    name = Column(String(255))

    @staticmethod
    def create_list_instance(user_id, name, shopping_list_data):
        db.session.begin()
        list_instance = ShoppingListInstance(
            user_id=user_id,
            name=name
        )
        db.session.add(list_instance)
        pre_class_list = Counter()
        for campus_id, cls_id, qty in shopping_list_data:
            pre_class_list[(campus_id, cls_id)] += int(qty)

        for key, qty in pre_class_list.items():
            campus_id, cls_id = key
            for item in db.session.query(ShoppingListItem)\
                    .filter(ShoppingListItem.shopping_list_id == cls_id)\
                    .filter(ShoppingListItem.active == True):
                list_instance.add_item(campus_id, item, quantity=qty)
        db.session.commit()
        return list_instance

    @staticmethod
    def create_list_instance_by_store(user_id, parent_list, name, stores):
        db.session.begin()

        list_instance = ShoppingListInstance(
            user_id=user_id,
            name=name or 'Untitled'
        )
        db.session.add(list_instance)
        db.session.flush()
        for item in parent_list.items:
            if item.market in stores:
                db.session.expunge(item)
                make_transient(item)
                item.id = None
                item.shopping_list_instance_id = list_instance.id
                item.is_one_off_item = True
                db.session.add(item)

        db.session.commit()
        return list_instance

    @property
    def markets(self):
        markets = [ market[0] for market in db.session.query(ShoppingListInstanceItem.market)\
                        .select_from(ShoppingListInstanceItem)\
                        .filter(ShoppingListInstanceItem.shopping_list_instance == self)\
                        .filter(ShoppingListInstanceItem.market != "")\
                        .filter(ShoppingListInstanceItem.got_it == 0)\
                        .distinct() ]
        return markets

    def get_items(self):
        return self.items.all()

    def get_item(self, campus_id, hsh):
        for item in self.items:
            if item.campus_id == campus_id and item.hash == hsh:
                return item
        return None

    def merge_lists(self, shopping_list_data):
        db.session.begin()

        pre_class_list = Counter()
        for campus_id, cls_id, qty in shopping_list_data:
            pre_class_list[(campus_id, cls_id)] += int(qty)

        for key, qty in pre_class_list.items():
            campus_id, cls_id = key
            for item in db.session.query(ShoppingListItem)\
                    .filter(ShoppingListItem.shopping_list_id == cls_id)\
                    .filter(ShoppingListItem.active == True):
                self.add_item(campus_id, item, quantity=qty)

        db.session.commit()

    def add_item(self, campus_id, item, quantity=1):
        # If the user enters a fraction, try to be slick and add correctly. This might be total overkill.
        num = item.mixed_number
        sli = self.get_item(campus_id, item.sli_hash)
        if sli is not None:
            sli.number += num * int(quantity)
        else:
            sli = ShoppingListInstanceItem(
                                campus_id=campus_id,
                                name=item.name,
                                number = num * int(quantity),
                                unit=item.unit,
                                market=item.market,
                                notes=item.notes,
                            )
            self.items.append(sli)
        sli.original_items.append(
            ShoppingListItemLink(
                shopping_list_item=item,
                quantity=quantity
            )
        )

    @property
    def aggregated_items(self):
        item_keys = {}
        for item in self.items:
            if u"{}:{}".format(item.name, item.unit) in item_keys:
                db.session.autoflush = False
                item_keys[u"{}:{}".format(item.name, item.unit)].number = \
                    str(item_keys[u"{}:{}".format(item.name, item.unit)].mixed_number + item.mixed_number)
            else:
                item_keys[u"{}:{}".format(item.name, item.unit)] = item

        return item_keys.values()


class ShoppingListInstanceItem(db.Model, MixedNumberItem):
    id = Column(Integer, primary_key=True)
    shopping_list_instance_id = Column(Integer, ForeignKey(ShoppingListInstance.id))
    campus_id = Column(Integer, ForeignKey(Campus.id), nullable=False)
    number = Column(String(5))
    unit = Column(String(25))
    name = Column(String(255))
    market = Column(String(255))
    notes = Column(String(255))
    got_it = Column(Boolean, default=False)
    checked_in = Column(Boolean, default=False)

    # for one-off items
    is_one_off_item = Column(Boolean, default=False)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=True)
    category = Column(String(10), nullable=True)

    shopping_list_instance = relationship(
        ShoppingListInstance, backref=backref("items", lazy="dynamic")
    )

    campus = relationship(Campus)

    @property
    def category_str(self):
        if self.is_one_off_item:
            if self.category:
                return ShoppingListItem.CATEGORIES[self.category]
            return 'None'
        return ShoppingListItem.CATEGORIES[self.original_items[0].shopping_list_item.category]

    @property
    def classes_str(self):
        if self.is_one_off_item:
            return ["{} ({})".format(self.class_abbr, self.number)]
        return ["{} ({})".format(oi.shopping_list_item.shopping_list.cls.abbr, oi.shopping_list_item.mixed_number * oi.quantity) for oi in self.original_items]

    @property
    def classes_no_items(self):
        if self.is_one_off_item:
            return ["{}".format(self.class_abbr)]
        return ["{}".format(oi.shopping_list_item.shopping_list.cls.abbr) for oi in self.original_items]

    @property
    def class_abbr(self):
        if self.is_one_off_item:
            if self.class_id:
                return Class.query.get(self.class_id).abbr
            return 'None'
        return self.original_items[0].shopping_list_item.shopping_list.cls.abbr


class ShoppingListItemLink(db.Model):
    __tablename__ = "shopping_list_instance_item_map"

    shopping_list_item_id = Column(Integer, ForeignKey(ShoppingListItem.id), primary_key=True)
    shopping_list_instance_item_id = Column(Integer, ForeignKey(ShoppingListInstanceItem.id), primary_key=True)
    quantity = Column(Integer)

    shopping_list_item = relationship(ShoppingListItem)
    shopping_list_instance_item = relationship(ShoppingListInstanceItem, backref="original_items")

    @property
    def mixed_number(self):
        return str(self.quantity * self.shopping_list_item.mixed_number)


class Subscriber(db.Model):
    __tablename__ = "Newsletter_subscriber"

    SUBSCRIBE_REASON_CHOICES = {
        'newsletter_signup': 'Signed up for newsletter',
        'class_signup': 'Signed up for class',
        'created_login': 'Created a login',
        'bought_gc': 'Bought a gift certificate',
        'received_gc': 'Received a gift certificate',
        'contact_page_email': 'Emailed from contact page',
        'admin_registered': 'Registered by admin'
    }

    id = Column(Integer, primary_key=True)
    email = Column(String(75))
    name = Column(String(255))
    campus_id = Column(Integer, ForeignKey(Campus.id))
    subscribe_reason = Column(Enum(*SUBSCRIBE_REASON_CHOICES.keys(), name="subscribe_reason"), nullable=False)
    created = Column("date_added", Date, default=date.today)
    active = Column(Boolean, default=True)

    campus = relationship(Campus)

    @property
    def gift_certificates_purchased(self):
        return db.session.query(GiftCertificate)\
                  .filter(GiftCertificate.sender_email == self.email)\
                  .all()

    @property
    def last_gift_certificate_purchased(self):
        return db.session.query(GiftCertificate)\
                  .filter(GiftCertificate.sender_email == self.email)\
                  .order_by(GiftCertificate.created.desc())\
                  .first()

    @property
    def readable_subscribe_reason(self):
        reason = self.SUBSCRIBE_REASON_CHOICES.get(self.subscribe_reason)
        if reason and self.subscribe_reason == 'bought_gc':
            if self.last_gift_certificate_purchased and self.last_gift_certificate_purchased.recipient_email:
                reason = reason + ' (Recipient: {})'.format(self.last_gift_certificate_purchased.recipient_email)
            else:
                reason = reason + ' (Recipient: {})'.format('unknown')
        return reason

    @staticmethod
    def subscribed(email):
        return bool(db.session.query(Subscriber).filter(Subscriber.email==email).all())

    @staticmethod
    def create_subscriber(email, name, campus_id, subscribe_reason):
        if not Subscriber.subscribed(email):
            db.session.begin(subtransactions=True)
            subscriber = Subscriber(email=email,
                                    name=name,
                                    campus_id=campus_id,
                                    subscribe_reason=subscribe_reason)
            db.session.add(subscriber)
            db.session.commit()

    def change_email(self, email):
        if self.email == email:
            return
        db.session.query(Subscriber).filter_by(email=email).delete()
        self.email = email


class ClassReport(db.Model):
    __tablename__ = "class_report"
    CLASS_CHOICES = OrderedDict((str(4-i), v) for i, v in enumerate((
        "--Select--",
        "Super-ridiculous fabulous fun",
        "About average: Really fun & great",
        "So-so",
        "Nota so gooda",
    )))
    ASSISTANT_CHOICES = OrderedDict((str(4-i), v) for i, v in enumerate((
        "--Select--",
        "Rockin' like Dokken",
        "Easy Listen'n",
        "Never again",
        "On my own & I am awesome",
    )))

    PACING_CHOICES = OrderedDict((str(2-i), v) for i, v in enumerate((
        "Perfecto!",
        "I had challenges with...",
    )))

    PREPREP_CHOICES = OrderedDict((str(2-i), v) for i, v in enumerate((
        "Awesome! I love me my prep crew!",
        "Here's a tip for next time...",
    )))

    BREAKAGE_CHOICES = OrderedDict((str(2-i), v) for i, v in enumerate((
        "I'm a Smooth Operator!",
        "Whoopsie, I had this issue...",
    )))

    SALES_CHOICES = OrderedDict((str(2-i), v) for i, v in enumerate((
        "All good!",
        "Please correct these sales for me...",
    )))

    TASTING_CHOICES = OrderedDict((str(3-i), v) for i, v in enumerate((
        "Manager taught class",
        "Nothing left",
        "Please taste!",
    )))

    id = Column(Integer, ForeignKey(Schedule.id), primary_key=True)
    class_rating = Column(Integer)
    attendance_rating = Column(Integer)
    assistant_rating = Column(Integer)
    group_comments = Column(Text)
    food_comments = Column(Text)
    pacing_rating = Column(Integer)
    pacing_comments = Column(Text)
    setup_review = Column(Text)
    tasting_rating = Column(Integer)
    tasting_comments = Column(Text)
    ingredients_problems = Column(Boolean)
    ingredients_comments = Column(Text)
    preprep_rating = Column(Integer)
    preprep_comments = Column(Text)
    breakage_rating = Column(Integer)
    breakage_comments = Column(Text)
    sales_rating = Column(Integer)
    sales_comments = Column(Text)
    created = Column(DateTime(timezone=True), default=datetime.utcnow)
    sent_on = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    draft = Column(Boolean, default=True)

    schedule = relationship(
        Schedule, backref=backref("report", lazy="dynamic")
    )

    # A bit of bitwise ORing for all those pesky multiselect statuses...
    @property
    def attendance_rating_list(self):
        lst = []
        for num in [1, 2, 4, 8]:
            if self.attendance_rating & num:
                lst.append(str(num))

        return lst if len(lst) > 0 else ["0"]

    @attendance_rating_list.setter
    def attendance_rating_list(self, val):
        attendance_rating = 0
        for rating in val:
            attendance_rating = attendance_rating | int(rating)
        self.attendance_rating = attendance_rating


class ClassReportComment(db.Model):
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey(ClassReport.id))
    teacher_id = Column(Integer, ForeignKey(Teacher.user_id))
    comment = Column(Text)
    created = Column(DateTime(timezone=True), default=datetime.utcnow)

    report = relationship(
        ClassReport, backref=backref("comments", lazy="dynamic")
    )
    teacher = relationship(Teacher)


class ExtraPerson(db.Model):
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey(Schedule.id))
    name = Column(String(50))
    email = Column(String(100))
    how_paid = Column(String(20))
    order_id = Column(Integer, ForeignKey(ScheduleOrder.id))

    schedule = relationship(
        Schedule, backref=backref("extra_people", lazy="dynamic")
    )

    original = relationship(
        ScheduleOrder, backref=backref("substitute", lazy="dynamic")
    )


class ProductOrder(db.Model):
    PAID_WITH_CHOICES = (
        ("In-storeCC", "In-Store CC", ),
        ("Cash", "Cash",),
        ("Check", "Check",),
        ("Call-in CC", "Call-in CC",),
        ("Freebie", "Freebie",),
        ("OnlineCC", "Online CC",),
    )
    PAID_WITH_CHOICES_ABBR = (
        ("In-storeCC", "In-Store CC", ),
        ("Cash", "Cash",),
        ("Check", "Check",),
    )
    __tablename__ = "Shop_productsale"

    id = Column(Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id), nullable=False)
    sold_by_id = Column(Integer, ForeignKey(Teacher.user_id))
    purchase_id = Column(Integer, ForeignKey(Purchase.id))
    online_sale = Column(Boolean, nullable=False)
    in_store_pickup = Column(Boolean, nullable=False)
    paid_with = Column(String(10))
    date_ordered = Column(DateTime(timezone=True), default=datetime.utcnow)
    date_sent = Column(DateTime(timezone=True), default=datetime.utcnow)
    shipped_by = Column(String(5))
    sender_name = Column(String(100))
    sender_email = Column(String(75))
    sender_phone = Column(String(20))
    name_on_envelope = Column(String(255))
    street_address = Column(String(255))
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    discount = Column(Integer, nullable=False, default=0)

    campus = relationship(Campus)

    sold_by = relationship(Teacher)

    purchase = relationship(Purchase, backref=backref("product_orders"))

    @property
    def subtotal(self):
        return sum([item.discounted_subtotal for item in self.items])

    @property
    def shipping(self):
        return sum([item.shipping for item in self.items])

    @property
    def tax(self):
        return sum([item.tax for item in self.items])

    @property
    def total_paid(self):
        return self.subtotal + self.shipping + self.tax

    @property
    def readable_sale_type(self):
        if self.online_sale:
            return 'Live Site Sale'
        return 'Admin Site Sale'

    def assign_products(self, campus, products, in_store_pickup, discount=0):
        for product, qty in products:
            item = ProductOrderItem(
                productsale_id=self.id,
                product_id=product.id,
                quantity=qty,
                shipping=product.shipping_price(qty, in_store_pickup),
                discounted_subtotal=(product.base_price(qty) *
                                     (1 - Decimal(discount)/100)),
                tax=product.tax_price(qty, self.campus.sales_tax, discount),
            )
            db.session.add(item)
            inv = ProductInventory.query.filter_by(
                    campus_id=campus.id,
                    product_id=product.id,
                ).first()
            if inv is not None:
                inv.quantity_stocked -= int(qty)
                db.session.merge(inv)
            else:
                logging.error("Product being sold has no inventory")

    def remove_items(self, items):
        db.session.begin(subtransactions=True)
        for order_item in items:
            product = order_item.product
            inv = ProductInventory.query.filter_by(
                    campus_id=self.campus.id,
                    product_id=product.id,
                ).first()
            if inv is not None:
                inv.quantity_stocked += int(order_item.quantity)
                db.session.merge(inv)
            else:
                logging.error("Product being sold has no inventory")
            db.session.delete(order_item)
        db.session.commit()


class ProductOrderItem(db.Model):
    __tablename__ = "Shop_productsaleitem"

    id = Column(Integer, primary_key=True)
    productsale_id = Column(Integer, ForeignKey(ProductOrder.id))
    product_id = Column(Integer, ForeignKey(Product.id))
    quantity = Column(Integer)
    shipping = Column(Numeric(6, 2))
    discounted_subtotal = Column(Numeric(6, 2))
    tax = Column(Numeric(6, 2))

    order = relationship(ProductOrder, backref=backref("items", cascade="all, delete-orphan"))
    product = relationship(Product)

    @staticmethod
    def sold(campus_id, product_id):
        sold = db.session.query(func.sum(ProductOrderItem.quantity))\
            .join(ProductOrder)\
            .filter(
                ProductOrder.campus_id == campus_id,
                ProductOrderItem.product_id == product_id,
            )\
            .one()[0]
        return sold if sold is not None else 0


class AdminNote(db.Model):
    id = Column(Integer, primary_key=True)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow(), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    note = Column(Text, nullable=False)

    user = relationship(User)


class ResourcesMarket(db.Model):
    MARKET_DATA = {
        "D": (
            "diy",
            "DIYers: Cheese-makers, homebrewers, cake-makers, gardeners, etc",
        ),
        "F": ("farmers", "Farmers Markets"),
        "M": ("meat", "Meat/Poultry/Seafood"),
        "P": ("produce", "Produce"),
        "S": ("spices", "Spices/Sundries/Staples"),
        "A": ("alcohol", "Wine, bottle shops, booze"),
        "E": ("ethnic", "Ethnic"),
    }

    id = Column(Integer, primary_key=True)
    campus_id = Column(Integer, ForeignKey(Campus.id))
    name = Column(String(255))
    address_1 = Column(String(512))
    address_2 = Column(String(512))
    description = Column(String(255))
    type_1 = Column(String(1))
    type_2 = Column(String(1))
    type_3 = Column(String(1))

    campus = relationship(Campus)

    @property
    def market_data(self):
        if self.type_1:
            yield self.MARKET_DATA[self.type_1]
        if self.type_2:
            yield self.MARKET_DATA[self.type_2]
        if self.type_3:
            yield self.MARKET_DATA[self.type_3]

    @property
    def classes(self):
        return [cls for cls, _name in self.market_data]

    @property
    def address(self):
        return Markup("{}<br>{}").format(self.address_1, self.address_2)


class ResourcesKitchen(db.Model):
    PICTURE_DIR = "resources-kitchen"
    PDF_DIR = "pdfs"

    CATEGORY_LARGE_APPLIANCES = "Large Appliances"
    CATEGORY_SMALL_APPLIANCES = "Small Appliances"
    SPECIAL_MANUFACTURERS = ('Miele', 'Vitamix')

    id = Column(Integer, primary_key=True)
    category = Column(String(31))
    picture = Column(String(255))
    link = Column(String(255))
    name = Column(String(255))
    manufacturer = Column(String(255))
    order = Column(Integer)

    @property
    def pic_url(self):
        if self.picture is None:
            return ""
        return utils.url_path(self.PICTURE_DIR, self.picture)

    @property
    def pdf_url(self):
        if self.category != self.CATEGORY_LARGE_APPLIANCES:
            logging.warn("Generating pdf url for non-Large-Appliance: %s",
                         self.id)
        return utils.url_path(self.PDF_DIR, self.link)


class ResourcesIngredients(db.Model):
    PICTURE_DIR = "resources-ingredients"

    id = Column(Integer, primary_key=True)
    picture = Column(String(255))
    name = Column(String(255))
    description = Column(String(255))
    order = Column(Integer)

    @property
    def pic_url(self):
        if self.picture is None:
            return ""
        return utils.url_path(self.PICTURE_DIR, self.picture)


class ForgotPasswordLinks(db.Model):
    code = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    expires = Column(DateTime(timezone=True), default=datetime.utcnow())
    used = Column(Boolean, server_default=literal(False))

    user = relationship(User)

    @classmethod
    def new(cls, user):
        return cls(
            code=b32encode(urandom(11))[:16].lower(),
            user=user,
            expires=datetime.utcnow + timedelta(days=1),
        )
