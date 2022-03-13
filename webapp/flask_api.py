#!/usr/bin/env python

import os
import json
import yaml
import logging
import logging.config
from datetime import datetime
from hashlib import md5
from flask import Flask, request, render_template, url_for, flash, redirect
from flask_login import LoginManager
from werkzeug.exceptions import abort

from db_utils import query

FLASK_APP_PORT = int(os.environ['FLASK_APP_PORT'])

# Configure logging
with open('logging_conf.yaml', 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))
logger = logging.getLogger('root')

# Create Flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['FLASK_SECRET_KEY']
logger.info('App initialized')

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(player_id):
    return User.get(player_id)

# Functions to return responses to various requests

# need helper fns to validate request structure

def player_exists(player_id):
    data = query('''SELECT MAX(CASE WHEN player_id = '{}' THEN TRUE ELSE FALSE END) as player_exists FROM players;'''.format(player_id))
    return data['player_exists']

def character_exists(character_id):
    data = query('''SELECT MAX(CASE WHEN character_id = '{}' THEN TRUE ELSE FALSE END) as character_exists FROM characters;'''.format(character_id))
    return data['character_exists']

@app.route('/')
def index():
    logger.debug('Request to index')
    return render_template('index.html')

@app.route('/home/<player_id>')
def home(player_id):
    logger.debug('Request to home')
    if not player_id or player_id == '':
        return redirect(url_for('index'))
    if not player_exists(player_id):
        abort(404)
    else:
        player_name = query('''SELECT DISTINCT player_name FROM players WHERE player_id = '{}';'''.format(player_id))['player_name']
    player_characters = query('''SELECT character_id, character_name, character_playbook FROM characters WHERE player_id = '{}';'''.format(player_id))
    if isinstance(player_characters, dict):
        player_characters = [player_characters]
    return render_template('home.html', name = player_name, chars = player_characters)

@app.route('/register', methods = ['GET','POST'])
def register():
    logger.debug('Request to register')
    if request.method == 'POST':
        player_name = request.form['name']
        logger.debug(f'Call to create_player for {player_name}')
        player_pass_raw = request.form['pass']
        player_pass_raw2 = request.form['pass2']
        if player_pass_raw != player_pass_raw2:
            flash('Passwords do not match')
        else:
            player_id = md5(player_name.encode()).hexdigest()
            if player_exists(player_id):
                flash('Player name {} already exists'.format(player_name))
            else:
                player_pass = md5(player_pass_raw.encode()).hexdigest()
                query('''INSERT INTO players (player_id, player_name, player_password_hash) VALUES ('{}','{}','{}');'''.format(player_id, player_name, player_pass), output = False)
                logger.debug(f'Inserted {player_id}')
                return redirect(url_for('home', player_id = player_id))
    return render_template('register.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    logger.debug('Request to login')
    if request.method == 'POST':
        logger.debug('Login for submitted')
        player_name = request.form['name'] 
        logger.debug(f'for {player_name}')
        req_pw = md5(request.form['pass'].encode()).hexdigest()
        logger.debug(f'request password: {req_pw}')
        data = query('''SELECT player_id, player_password_hash FROM players WHERE player_name = '{}';'''.format(player_name)) 
        player_id = data['player_id']
        player_pw = data['player_password_hash']
        logger.debug(f'db password: {player_pw}')
        if req_pw != player_pw:
            flash('Incorrect player name or password.')
            logger.debug('Failed attempt')
        else:
            logger.debug('Successful attempt')
            return redirect(url_for('home', player_id = player_id))

    return render_template('login.html')

# API functions should eventually live in their own file, and probably be class methods
@app.route('/api/player', methods = ['GET'])
def get_player_names():
    logger.debug('Call to get_player_names')
    data = query('''SELECT DISTINCT player_name FROM players;''')
    resp = {'status': 'success', 'data': data}
    if data:
        logger.debug(f'Returned {data}')
    else:
        logger.error(f'Empty Return {data}')
    return json.dumps(resp)

@app.route('/api/player/create', methods = ['POST'])
def create_player():
    ''' docstring '''
    player_name = request.args.get('name')
    logger.debug(f'Call to create_player for {player_name}')
    player_pass = request.args.get('pass')
    player_id = md5(player_name.encode()).hexdigest()
    query('''INSERT INTO players (player_id, player_name, player_password_hash) VALUES ('{}','{}','{}');'''.format(player_id, player_name, player_pass), output = False)
    resp = {
        'status': 'success',
        'data': {
            'player_id': player_id
        }
    }
    logger.debug(f'Inserted {player_id}')
    return json.dumps(resp)

@app.route('/api/player/login', methods = ['POST']) # {flask_host}/login?name={player_name}&pass={password_hash}
def login_player():
    ''' ZZ docstring '''
    logger.debug('Call to login')
    player_name = request.args.get('name') 
    logger.debug(f'for {player_name}')
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
        logger.debug('Failed attempt')
    else:
        resp = {
            'status': 'success',
            'message': 'Logged in as {}.'.format(player_name),
            'data': {'player_id': player_id}
        }
        logger.debug('Successful attempt')
    return json.dumps(resp)

@app.route('/character')
def character():
    pass

@app.route('/api/character/create', methods = ['POST']) 
def create_character():
    ''' ZZ docstring '''
    logger.debug('Call to create_character')
    player_id = request.args.get('user')
    logger.debug(f'for {player_id}')
    character_name = request.args.get('cname')
    character_id = md5((player_id + character_name).encode()).hexdigest() 
    if character_exists(character_id):
        resp = {'status': 'failure', 'message': 'Character already exists', 'data': {}}
        logger.debug('Duplicate character found')
    else:
        query('''INSERT INTO characters (player_id, character_id, character_name) VALUES ('{}','{}','{}');'''.format(player_id, character_id, character_name), output = False)
        query('''INSERT INTO character_moves (SELECT '{}', move_id FROM moves WHERE move_type IN ('Basic','Balance','Advancement'));'''.format(character_id), output = False)
        query('''INSERT INTO character_techniques (SELECT '{}', technique_id, 'Basic' FROM techniques WHERE technique_type = 'Basic');'''.format(character_id), output = False)
        resp = {'status': 'success', 'data': {'character_id': character_id}}
        logger.debug(f'{character_name} created')
    return json.dumps(resp)

@app.route('/api/character', methods = ['GET'])
def get_character_data():
    ''' docstring '''
    logger.debug('Call to get_character_data')
    c_id = request.args.get('id')
    data = query('''SELECT * FROM characters WHERE character_id = '{}';'''.format(c_id))
    data = {k: v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else v for k,v in data.items()}
    resp = {'status': 'success', 'data': data}
    logger.debug(f'Returned {data}')
    return json.dumps(resp)

@app.route('/api/character', methods = ['POST']) 
def update_character():
    ''' ZZ docstring '''
    logger.debug('Call to update_character')
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
    logger.debug('Character updated')
    return get_character_data()

@app.route('/api/playbook', methods = ['GET'])
def get_playbook():
    ''' docstring '''
    logger.debug('Call to get_playbook')
    p_id = request.args.get('id')
    if not p_id:
        data = query('''SELECT * FROM playbooks;''')
        logger.debug('Returned all')
    else:
        data = query('''SELECT * FROM playbooks WHERE playbook_id = '{}';'''.format(p_id))
        logger.debug(f'Returned {p_id}')
    resp = {'status': 'success', 'data': data}
    logger.debug(f'Returned {data}')
    return json.dumps(resp)

@app.route('/api/technique', methods = ['GET'])
def get_technique():
    ''' docstring '''
    logger.debug('Call to get_technique')
    t_id = request.args.get('id')
    if not t_id:
        data = query('''SELECT * FROM techniques;''')
        logger.debug('Returned all')
    else:
        data = query('''SELECT * FROM techniques WHERE technique_id = '{}';'''.format(t_id))
        logger.debug(f'Returned {t_id}')
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/move', methods = ['GET'])
def get_move():
    ''' docstring '''
    logger.debug('Call to get_move')
    m_id = request.args.get('id')
    if not m_id:
        data = query('''SELECT * FROM moves;''')
        logger.debug('Returned all')
    else:
        data = query('''SELECT * FROM moves WHERE move_id = '{}';'''.format(m_id))
        logger.debug(f'Returned {m_id}')
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/character/moves', methods = ['GET'])
def get_character_moves():
    ''' docstring '''
    logger.debug('Call to get_character_moves')
    c_id = request.args.get('id')
    data = query('''SELECT c.character_id, m.* FROM character_moves c JOIN moves m ON c.move_id = m.move_id WHERE c.character_id = '{}';'''.format(c_id))
    resp = {'status': 'success', 'data': data}
    logger.debug(f'Returned {data}')
    return json.dumps(resp)

@app.route('/api/character/moves', methods = ['POST'])
def add_character_move():
    ''' docstring '''
    logger.debug('Call to add_character_move')
    c_id = request.args.get('id')
    m_id = request.args.get('mid')
    query('''INSERT INTO character_moves VALUES ('{}', '{}');'''.format(c_id, m_id), output = False)
    resp = {'status': 'success', 'data': {}}
    logger.debug(f'Inserted {m_id} for {c_id}')
    return json.dumps(resp)

@app.route('/api/character/techniques', methods = ['GET'])
def get_character_techniques():
    ''' docstring '''
    logger.debug('Call to get_character_techniques')
    c_id = request.args.get('id')
    data = query('''SELECT c.character_id, c.technique_mastery, t.* FROM character_techniques c JOIN techniques t ON c.technique_id = t.technique_id WHERE c.character_id = '{}';'''.format(c_id))
    resp = {'status': 'success', 'data': data}
    logger.debug('Returned {data.technique_mastery} for {data.character_id}')
    return json.dumps(resp)

@app.route('/api/character/techniques', methods = ['POST'])
def add_character_technique():
    ''' docstring '''
    logger.debug('Call to add_character_technique')
    c_id = request.args.get('id')
    t_id = request.args.get('tid')
    mastery = request.args.get('mastery')
    if not mastery:
        mastery = 'Learned'
    query('''INSERT INTO character_techniques VALUES ('{}', '{}', '{}');'''.format(c_id, t_id, mastery), output = False)
    resp = {'status': 'success', 'data': {}}
    logger.debug(f'{c_id} has learned {t_id}')
    return json.dumps(resp)


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = FLASK_APP_PORT)