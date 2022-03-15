#!/usr/bin/env python

import os
from application import app

FLASK_APP_PORT = int(os.environ['FLASK_APP_PORT'])

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = FLASK_APP_PORT)