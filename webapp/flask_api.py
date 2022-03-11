#!/usr/bin/env python

import os
import json
from datetime import datetime
from hashlib import md5
from flask import Flask, request

from db_utils import query

FLASK_APP_PORT = int(os.environ['FLASK_APP_PORT'])

# Create Flask app instance
app = Flask(__name__)

# Functions to return responses to various requests

# need helper fns to validate request structure

@app.route('/')
def default():
    resp = {'status': 'success', 'message': 'default response'}
    return json.dumps(resp)

@app.route('/players', methods = ['GET'])
def get_player_names():
    data = query('''SELECT DISTINCT player_name FROM players;''')
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/register', methods = ['POST'])
def create_player():
    ''' docstring '''
    player_name = request.args.get('name')
    player_pass = request.args.get('pass')
    player_id = md5(player_name.encode()).hexdigest()
    query('''INSERT INTO players (player_id, player_name, player_password_hash) VALUES ('{}','{}','{}');'''.format(player_id, player_name, player_pass), output = False)
    resp = {
        'status': 'success',
        'data': {
            'player_id': player_id
        }
    }
    return json.dumps(resp)

@app.route('/login', methods = ['POST']) # {flask_host}/login?name={player_name}&pass={password_hash}
def login():
    ''' ZZ docstring '''
    player_name = request.args.get('name') 
    req_pw = request.args.get('pass')
    data = query('''SELECT player_id, player_password_hash FROM players WHERE player_name = '{}';'''.format(player_name)) 
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
            'message': 'Logged in as {}.'.format(player_name),
            'data': {'player_id': player_id}
        }
    return json.dumps(resp)

@app.route('/character/create', methods = ['POST']) 
def create_character():
    ''' ZZ docstring '''
    player_id = request.args.get('user')
    character_name = request.args.get('cname')
    character_id = md5((player_id + character_name).encode()).hexdigest()
    data = query('''SELECT MAX(CASE WHEN character_id = '{}' THEN TRUE ELSE FALSE END) as character_exists FROM characters;''')
    if data['character_exists']:
        resp = {'status': 'failure', 'message': 'Character already exists', 'data': {}}
    else:
        query('''INSERT INTO characters (player_id, character_id, character_name) VALUES ('{}','{}','{}');'''.format(player_id, character_id, character_name), output = False)
        query('''INSERT INTO character_moves (SELECT '{}', move_id FROM moves WHERE move_type IN ('Basic','Balance','Advancement'));'''.format(character_id), output = False)
        query('''INSERT INTO character_techniques (SELECT '{}', technique_id, 'Basic' FROM techniques WHERE technique_type = 'Basic');'''.format(character_id), output = False)
        resp = {'status': 'success', 'data': {'character_id': character_id}}
    return json.dumps(resp)

@app.route('/character', methods = ['GET'])
def get_character_data():
    ''' docstring '''
    c_id = request.args.get('id')
    data = query('''SELECT * FROM characters WHERE character_id = '{}';'''.format(c_id))
    data = {k: v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else v for k,v in data.items()}
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/character', methods = ['POST']) 
def update_character():
    ''' ZZ docstring '''
    character_id = request.args.get('id')
    # confirm character id exists
    upd = []
    for k, v in request.args.items():
        # check k is valid character property
        if k == 'id':
            continue
        elif k == 'playbook':
            upd.append('''character_playbook_id = (SELECT playbook_id FROM playbooks WHERE playbook = '{}')'''.format(v))
        vals = "character_{} = '{}'".format(k, v) if isinstance(v, str) else 'character_{} = {}'.format(k, v)
        upd.append(vals)
    upd.append('character_updated_at = CURRENT_TIMESTAMP()')
    query('''UPDATE characters SET {} WHERE character_id = '{}';'''.format(', '.join(upd), character_id), output = False)
    return get_character_data()

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

@app.route('/technique', methods = ['GET'])
def get_technique():
    ''' docstring '''
    t_id = request.args.get('id')
    if not t_id:
        data = query('''SELECT * FROM techniques;''')
    else:
        data = query('''SELECT * FROM techniques WHERE technique_id = '{}';'''.format(t_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/move', methods = ['GET'])
def get_move():
    ''' docstring '''
    m_id = request.args.get('id')
    if not m_id:
        data = query('''SELECT * FROM moves;''')
    else:
        data = query('''SELECT * FROM moves WHERE move_id = '{}';'''.format(m_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/character/moves', methods = ['GET'])
def get_character_moves():
    ''' docstring '''
    c_id = request.args.get('id')
    data = query('''SELECT c.character_id, m.* FROM character_moves c JOIN moves m ON c.move_id = m.move_id WHERE c.character_id = '{}';'''.format(c_id))
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/character/moves', methods = ['POST'])
def add_character_move():
    ''' docstring '''
    c_id = request.args.get('id')
    m_id = request.args.get('mid')
    query('''INSERT INTO character_moves VALUES ('{}', '{}');'''.format(c_id, m_id), output = False)
    resp = {'status': 'success', 'data': {}}
    return json.dumps(resp)

@app.route('/character/techniques', methods = ['GET'])
def get_character_techniques():
    ''' docstring '''
    c_id = request.args.get('id')
    data = query('''SELECT c.character_id, c.technique_mastery, t.* FROM character_techniques c JOIN techniques t ON c.technique_id = t.technique_id WHERE c.character_id = '{}';'''.format(c_id))
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
    app.run(host = '0.0.0.0', port = FLASK_APP_PORT)