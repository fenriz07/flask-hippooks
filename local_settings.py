import os

DEBUG = True
ADMINS = frozenset(['Darin@Molnar.com.com'])

DB_USER = "root"
DB_PASS = "6419148"
DB_NAME = "hipcooks"

URL = "localhost"

SQLALCHEMY_DATABASE_URI = "mysql://%s:%s@localhost/%s"%(DB_USER, DB_PASS, DB_NAME)
DATABASE_CONNECT_OPTIONS = ()


# email server
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_SENDER = None
