#!/usr/bin/env python

import time
import os
import pymysql

# Set up database connection
DB_USER = os.environ['MYSQL_DB_USER'] 
DB_PASS = os.environ['MYSQL_DB_PASS'] 
DB_PORT = int(os.environ['MYSQL_DB_PORT'])

def establish_connection(wait_time = 2, max_wait_time = 600):
    connected = False
    connection = None
    tot_wait_time = 0
    while not connected and tot_wait_time <= max_wait_time:
        try:
            connection = pymysql.connect(
                user = DB_USER,
                password = DB_PASS,
                host = 'mysql',
                port = DB_PORT,
                database = 'avatar',
                cursorclass = pymysql.cursors.DictCursor,
                autocommit = True
            )
            connected = True
        except pymysql.err.OperationalError:
            time.sleep(wait_time)
            tot_wait_time += wait_time
    if not connection:
        print('Unable to establish database connection.')
        raise SystemExit
    return connection

connection = establish_connection()

def query(query_text, output = True, connection = connection):
    result = None
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query_text)
            if output:
                result = cursor.fetchall()
    return result