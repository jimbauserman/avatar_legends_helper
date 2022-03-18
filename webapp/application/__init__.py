#!/usr/bin/env python

import os
import logging
import logging.config
import yaml
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

FLASK_SECRET_KEY = os.environ['FLASK_SECRET_KEY']
DB_USER = os.environ['MYSQL_DB_USER'] 
DB_PASS = os.environ['MYSQL_DB_PASS'] 
DB_PORT = os.environ['MYSQL_DB_PORT']
DB_URI = 'mysql+pymysql://{}:{}@mysql:{}/avatar'.format(DB_USER, DB_PASS, DB_PORT)

with open('application/logging_conf.yaml', 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))
logger = logging.getLogger(__name__)

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """Construct the core application."""
    app = Flask(__name__)

    app.config['SECRET_KEY'] = FLASK_SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    return app

app = create_app()
with app.app_context():
    from . import routes  # Import routes
    from . import db_model # Import database model
logger.info('App initialized')