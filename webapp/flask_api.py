#!/usr/bin/env python

import os
import json
from flask import Flask
from flask import request

from db_utils import query

# Create Flask app instance
app = Flask(__name__)

# Functions to return responses to various requests

# need helper fns to validate request structure

@app.route('/')
def default():
    resp = {'status': 'success', 'message': 'default response'}
    return json.dumps(resp)

@app.route('/login', methods = ['GET','POST']) # {flask_host}/login?name={player_name}&pass={password_hash}
def login():
    ''' ZZ docstring '''
    player = request.args.get('name') 
    req_pw = request.args.get('pass')
    data = query('''SELECT player_id, player_password_hash FROM players WHERE player_name = '{}';'''.format(player)) 
    player_id = data['player_id']
    player_pw = data['player_password_hash']
    if req_pw != player_pw:
        resp = {
            'status': 'failure',
            'message': 'Incorrect player name or password.',
            'data': {}
        }
    else:
        resp = {
            'status': 'success',
            'message': 'Logged in as {}.'.format(player),
            'data': {'player_id': player_id}
        }
    return json.dumps(resp)

@app.route('/character', methods = ['POST']) 
def create_character():
    ''' ZZ docstring '''
    player_id = request.args.get('player')
    character_name = request.args.get('cname')
    character_id = None #some kind of UUID or content hash
    # Optional args
    pass

@app.route('/character', methods = ['GET'])
def get_character_data():
    ''' docstring '''
    c_id = request.args.get('id')
    data = query('''SELECT * FROM characters WHERE character_id = '{}';'''.format(c_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/playbook', methods = ['GET'])
def get_playbook():
    ''' docstring '''
    p_id = request.args.get('id')
    if not p_id:
        data = query('''SELECT * FROM playbooks;''')
    else:
        data = query('''SELECT * FROM playbooks WHERE playbook_id = '{}';'''.format(p_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/character/moves', methods = ['GET'])
def get_character_moves():
    ''' docstring '''
    c_id = request.args.get('id')
    data = query('''SELECT c.character_id, m.* FROM character_moves c JOIN moves m ON c.move_id = m.move_id WHERE c.character_id = '{}';'''.format(c_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/character/techniques', methods = ['GET'])
def get_character_techniques():
    ''' docstring '''
    c_id = request.args.get('id')
    data = query('''SELECT c.character_id, c.technique_mastery, t.* FROM character_techniques c JOIN techniques t ON c.technique_id = m.technique_id WHERE c.character_id = '{}';'''.format(c_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/character/techniques', methods = ['POST'])
def add_character_technique():
    ''' docstring '''
    c_id = request.args.get('id')
    t_id = request.args.get('tid')
    mastery = request.args.get('mastery')
    if not mastery:
        mastery = 'Learned'
    query('''INSERT INTO character_techniques VALUES ('{}', '{}', '{}');'''.format(c_id, t_id, mastery), output = False)
    resp = {'status': 'success', 'data': {}}
    return json.dumps(resp)


if __name__ == '__main__':
    app.run(host = '0.0.0.0')