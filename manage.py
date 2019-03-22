#!/usr/bin/env python

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from hipcooks.commands.assistant_credit_and_gc_award import AssistantCreditAndGiftCertificateAward
from hipcooks import settings

app = Flask(__name__)
app.secret_key = settings.SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
app.config['UPLOAD_FOLDER'] = settings.UPLOAD_FOLDER

db = SQLAlchemy(app)
from hipcooks import *
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('assistant_credit_and_gc_award', AssistantCreditAndGiftCertificateAward())


@manager.command
def captchas():
    with app.app_context():
        import os
        try:
            os.makedirs(app.config["CAPTCHA_PREGEN_PATH"])
        except os.error as e:
            logging.info(e)
        generate_images(app.config["CAPTCHA_PREGEN_MAX"])


if __name__ == '__main__':
    manager.run()
