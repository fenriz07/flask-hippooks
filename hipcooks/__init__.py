from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CsrfProtect
#from fractions import Fraction
import re
#from werkzeug.serving import run_simple
import settings
from flask.ext.mail import Mail

csrf = CsrfProtect()
app = Flask(__name__)

app.config.from_object(settings)
app.config.update(
    DEBUG           = settings.DEBUG,
    MAIL_SERVER     = settings.MAIL_SERVER,
    MAIL_PORT       = settings.MAIL_PORT,
    MAIL_USE_SSL    = settings.MAIL_USE_SSL,
    MAIL_USE_TLS    = settings.MAIL_USE_TLS,
    MAIL_USERNAME   = settings.MAIL_USERNAME,
    MAIL_PASSWORD   = settings.MAIL_PASSWORD,
    MAIL_SENDER     = settings.MAIL_SENDER
    )

mail=Mail(app)

csrf.init_app(app)

db = SQLAlchemy(app, session_options={"autocommit": True})
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config["WTF_CSRF_ENABLED"] = False

import logging
from logging.handlers import RotatingFileHandler
app.logger.setLevel(logging.DEBUG)

#from hipcooks import models
from public import *
from public.views import blueprint as public_views
from admin.views import blueprint as admin_views

csrf.exempt(admin_views)
app.register_blueprint(public_views)
app.register_blueprint(admin_views)

if settings.DEBUG:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication( app.wsgi_app, True )

@csrf.error_handler
def csrf_error(reason):
    return render_template('/errors/csrf_error.html', reason=reason), 400

@app.errorhandler(404)
def not_found(error):
    return render_template('/errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('/errors/500.html'), 500

@app.template_filter('mixed')
def mixed_number_filter(num):
    fract = re.match(r"^(\d+)\s*/\s*(\d+)$", str(num))
    if fract:
        numerator = int(fract.group(1))
        denominator = int(fract.group(2))
        if numerator > denominator and numerator % denominator != 0:
            return "{} {}/{}".format(numerator / denominator, numerator % denominator, denominator)
    return num

@app.template_filter('makedistinct')
def make_distinct_filter(s):
    return ", ".join(set(str(s).split(",")))

