#!/usr/bin/env python
#from flask import Flask
from hipcooks import app, db
from socket import gethostname

#app = Flask(__name__)

if __name__ == '__main__':
    db.metadata.create_all(db.engine)
    if 'liveconsole' not in gethostname():
        app.run()