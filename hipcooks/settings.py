import os
#_basedir = "/home/DrDarin/hipcooks/"
_basedir = "/home/fen/Freelancer/Clientes/hipcooks/proyect/"

DEBUG = True
CREDIT_CARD_DEBUG = DEBUG
ADMINS = frozenset(['Darin@Molnar.com'])
SECRET_KEY = 'brXtnG1zveapp4TuLr'
SALT = "dfas86gdf87af8abf8f8ab8g8ast86qwt3812g812ebe2"

URL = "localhost"

SQLALCHEMY_DATABASE_URI = "mysql://root:123456@localhost/hipcooks"
SQLALCHEMY_POOL_RECYCLE = 280
SQLALCHEMY_POOL_TIMEOUT = 20
DB_USER = "root"
DB_PASS = "123456"
DB_NAME = "hipcooks"

UPLOAD_FOLDER_NAME = "uploads"
UPLOAD_FOLDER = os.path.join(_basedir, UPLOAD_FOLDER_NAME)
DATABASE_CONNECT_OPTIONS = {}

# email server
MAIL_SERVER = 'smtp.smtp2go.com'
MAIL_PORT = 2525
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = "Darin@Molnar.com"
MAIL_PASSWORD = "oj8rBLzjERub"
MAIL_SENDER = "hipcookstesting@gmail.com"

if MAIL_USERNAME and MAIL_SERVER:
    MAIL_EMAIL_ADDRESS = MAIL_USERNAME + '@' + MAIL_SERVER
else:
    MAIL_EMAIL_ADDRESS = None

RECAPTCHA_PUBLIC_KEY = "6Lciww8UAAAAAE7Xr5fSIuWM6a7zqYGJHWitaXGm"
RECAPTCHA_PRIVATE_KEY = "6Lciww8UAAAAAB56GUDnKdkRzovuu8jCXcHctTFt"
RECAPTCHA_OPTIONS = dict(
    theme='custom',
    custom_theme_widget='recaptcha_widget'
)
#CAPTCHA_PREGEN_PATH = "/public/captcha"
#CAPTCHA_PREGEN_MAX = 100

HIPCOOKS_REQUEST_EMAIL_ADDRESS = "darinmolnar@gmail.com"
HIPCOOKS_CONTACT_EMAIL_ADDRESS = HIPCOOKS_REQUEST_EMAIL_ADDRESS

#HIPCOOKS_WIKI_URL = "http://hipcooksdocs.parthenonsoftware.com/"

CANCELLATION_FEE = 5.00

SHOPPING_CART_TIMEOUT_MINUTES = 5

GROUP_MACROS = [
    {
        "name": "Regional Manager",
        "perms": {
            "schedule": {"view": True, "update": True},
            "schedule_report": {"view": True, "update": True},
            "class": {"view": True, "update": False},
            "class_recipes": {"view": True, "update": False},
            "class_setups": {"view": True, "update": True},
            "class_shoplists": {"view": True, "update": True},
            "shoplist_generate": {"view": True, "update": True},
            "shoplist_shop": {"view": True, "update": True},
            "shoplist_check": {"view": True, "update": True},
            "shoplist_delete": {"view": True, "update": True},
            "reports": {"view": True, "update": True},
            "subscriber_list": {"view": True, "update": False},
            "content": {"view": True, "update": True},
            "make_sale": {"view": True, "update": True},
            "sales_edit": {"view": True, "update": True},
            "product": {"view": True, "update": True},
            "staff": {"view": True, "update": True},
            "giftcertificate": {"view": True, "update": True},
            "preprep_list": {"view": True, "update": True},
            "photo_album_delete": {"view": True, "update": True},
            "press": {"view": True, "update": True},
         }
    },
    {
        "name": "Studio Manager",
        "perms": {
            "schedule": {"view": True, "update": True},
            "schedule_report": {"view": True, "update": True},
            "class": {"view": True, "update": False},
            "class_recipes": {"view": True, "update": False},
            "class_setups": {"view": True, "update": False},
            "class_shoplists": {"view": True, "update": False},
            "shoplist_generate": {"view": True, "update": True},
            "shoplist_shop": {"view": True, "update": True},
            "shoplist_check": {"view": True, "update": True},
            "shoplist_delete": {"view": True, "update": True},
            "content": {"view": True, "update": True},
            "make_sale": {"view": True, "update": True},
            "sales_edit": {"view": True, "update": True},
            "teacher_sales": {"view": True, "update": True},
            "product": {"view": True, "update": True},
            "staff": {"view": True, "update": True},
            "giftcertificate": {"view": True, "update": True},
            "preprep_list": {"view": True, "update": True},
            "photo_album_delete": {"view": True, "update": True},
            "press": {"view": True, "update": True},
         }
    },
    {
        "name": "Teacher",
        "perms": {
            "schedule": {"view": True, "update": False},
            "schedule_report": {"view": True, "update": False},
            "class": {"view": True, "update": False},
            "class_recipes": {"view": True, "update": False},
            "class_setups": {"view": True, "update": False},
            "class_shoplists": {"view": True, "update": False},
            "shoplist_generate": {"view": True, "update": True},
            "shoplist_shop": {"view": True, "update": True},
            "shoplist_check": {"view": True, "update": True},
            "make_sale": {"view": True, "update": True},
            "sales_edit": {"view": True, "update": False},
            "teacher_sales": {"view": True, "update": True},
            "staff": {"view": True, "update": False},
            "giftcertificate": {"view": True, "update": False},
            "preprep_list": {"view": True, "update": True},
            "press": {"view": False, "update": False},
         }
    },
    {
        "name": "Shop/Prep",
        "perms": {
            "schedule": {"view": True, "update": False},
            "schedule_report": {"view": True, "update": False},
            "class": {"view": True, "update": False},
            "class_recipes": {"view": True, "update": False},
            "class_setups": {"view": True, "update": False},
            "make_sale": {"view": True, "update": True},
            "sales_edit": {"view": True, "update": False},
            "product": {"view": False, "update": False},
            "press": {"view": False, "update": False},
        }
    },
    {
        "name": "Bartender",
        "perms": {
            "schedule": {"view": True, "update": False},
            "schedule_report": {"view": True, "update": False},
            "class": {"view": True, "update": False},
            "class_recipes": {"view": True, "update": False},
            "class_setups": {"view": True, "update": False},
            "make_sale": {"view": True, "update": True},
            "sales_edit": {"view": True, "update": False},
            "teacher_sales": {"view": True, "update": True},
            "press": {"view": False, "update": False},
         }
    },
    {
        "name": "Assistant",
        "perms": {
            "schedule": {"view": True, "update": False},
            "schedule_report": {"view": True, "update": False},
            "assistant_schedule_signup": {"view": True, "update": True},
            "press": {"view": False, "update": False},
        }
    },
    {
        "name": "Press",
        "perms": {
            "press": {"view": True, "update": True},
        }
    },
    {
        "name": "None",
        "perms": {}
    },
]

try:
    from settings import *
except ImportError:
    pass
