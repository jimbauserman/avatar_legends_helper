#!/usr/bin/env python

import os
from application import app

FLASK_APP_HOST = os.environ['FLASK_APP_HOST']
FLASK_APP_PORT = int(os.environ['FLASK_APP_PORT'])

if __name__ == '__main__':
    app.run(host = FLASK_APP_HOST, port = FLASK_APP_PORT)