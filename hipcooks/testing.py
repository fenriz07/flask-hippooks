from fixture import SQLAlchemyFixture, NamedDataStyle, DataTestCase
from flask.ext.testing import TestCase
from hipcooks import app, db, models
import shutil
import tempfile

class DatabaseTestCase(DataTestCase, TestCase):
    datasets = []

    def create_app(self):
        app.config['TESTING'] = True
        app.config["DB_NAME"] = "testing"
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "mysql://%s:%sDrDarin.mysql.pythonanywhere-services.com%s"%(app.config["DB_USER"],
                                          app.config["DB_PASS"],
                                          app.config["DB_NAME"]))
        app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
        app.config["PROPAGATE_EXCEPTIONS"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        return app

    def setUp(self):
        db.create_all()
        if len(self.datasets) > 0:
            self.fixture = SQLAlchemyFixture(
                env=models,
                style=NamedDataStyle(),
                engine=db.engine,
            )
            super(DatabaseTestCase, self).setUp()
        app.config["UPLOAD_FOLDER"] = tempfile.mkdtemp()
        db.session.begin(subtransactions=True)

    def tearDown(self):
        db.session.rollback()
        if len(self.datasets) > 0:
            super(DatabaseTestCase, self).tearDown()
        shutil.rmtree(app.config["UPLOAD_FOLDER"])
        db.session.remove()
        db.drop_all()
