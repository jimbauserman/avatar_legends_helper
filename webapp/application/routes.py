#!/usr/bin/env python

import os
import json
import logging
from datetime import datetime
from hashlib import md5
from flask import request, render_template, url_for, flash, redirect, abort
from flask_login import current_user, login_user, login_required
from is_safe_url import is_safe_url

from . import app, db, login_manager
from .db_model import *

FLASK_APP_HOST = os.environ['FLASK_APP_HOST']

logger = logging.getLogger('routes')

# need helper fns to validate request structure

# configure login 
@login_manager.user_loader
def load_user(id):
    return Player.get(id)
login_manager.login_view = 'login'

@app.route('/')
def index():
    logger.debug('Request to index')
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    logger.debug('Request to home')
    return render_template('home.html', player = current_user)

@app.route('/register', methods = ['GET','POST'])
def register():
    # try https://flask.palletsprojects.com/en/2.0.x/patterns/wtforms/
    logger.debug('Request to register')
    if request.method == 'POST':
        player_name = request.form['name']
        logger.debug(f'Call to create_player for {player_name}')
        player_pass_raw = request.form['pass']
        player_pass_raw2 = request.form['pass2']
        if player_pass_raw != player_pass_raw2:
            flash('Passwords do not match')
        else:
            if Player.get_name(player_name):
                flash('''Player name {name} already exists. <a href="{url}">Login here.</a>'''.format(name = player_name, url = url_for('login')))
            else:
                player = Player(player_name, player_pass_raw)
                db.session.add(player)
                db.session.commit()
                logger.debug(f'Inserted {player.id}')
                login_user(player)
                return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods = ['GET','POST'])
def login():
    logger.debug('Request to login')
    if request.method == 'POST':
        logger.debug('Login for submitted')
        player_name = request.form['name'] 
        logger.debug(f'for {player_name}')
        req_pw = md5(request.form['pass'].encode()).hexdigest()
        player = Player.get_name(player_name)
        if not player:
            flash('''No player with that name exists. <a href="{url}">Sign up here!</a>'''.format(url = url_for('register')))
        else:
            if req_pw != player.password_hash:
                flash('Incorrect player name or password.')
                logger.debug('Failed attempt')
            else:
                logger.debug('Successful attempt')
                login_user(player)
                # handle if user was redirected to login
                next = request.args.get('next')
                if next and not is_safe_url(next, {FLASK_APP_HOST}):
                    return abort(400)
                return redirect(next or url_for('home'))

    return render_template('login.html')

@app.route('/character')
def character():
    pass

@app.route('/character/create', methods = ['GET','POST'])
@login_required
def create_character():
    ''' ZZ docstring '''
    logger.debug('Call to create_character')
    player = current_user
    playbooks = Playbook.get_all()
    if request.method == 'POST':
        character_name = request.form['name']
        character = Character.get_name(player.id, character_name)
        if character:
            flash('You already have a character with that name')
        else:
            character = Character(player, character_name)
            character.playbook_id = request.form['playbook_id']
            db.session.add(character)
            for move in Move.starting_moves():
                cm = CharacterMove(character, move)
                db.session.add(cm)
            for technique in Technique.starting_techniques():
                ct = CharacterTechnique(character, technique)
                db.session.add(ct)
            db.session.commit()
            logger.debug(f'{character.name} created')
            return redirect(url_for('edit_character', step = 1, character_id = character.id))
    return render_template('character_create.html', playbooks = playbooks)

@app.route('/character/<character_id>/edit/<int:step>', methods = ['GET','POST']) 
@login_required
def edit_character(character_id, step):
    ''' ZZ docstring '''
    logger.debug('Call to edit_character')
    character = Character.get(character_id)
    data = {
        'statistics': statistics, # all these should ref to db model class that has description
        'trainings': trainings,
        'backgrounds': backgrounds, 
        'nations': nations,
        'techniques': Technique.query.filter_by(technique_type = 'Advanced').all()
    }
    if request.method == 'POST':
        for k, v in request.form.items():
            if k == 'stat':
                for s in statistics:
                    default = character.playbook.stats[s]
                    val = default + 1 if v == s else default
                    character.set(s.lower(), val)
            elif k in ['demeanors','history_questions','connections']: # JSON attributes
                val = json.dumps(request.form.getlist(k))
                character.set(k, val)
            elif k == 'moves':
                for move_id in request.form.getlist(k):
                    move = Move.get(move_id)
                    cm = CharacterMove(character, move)
                    db.session.add(cm)
            elif k == 'learned_technique':
                technique = Technique.get(v)
                ct = CharacterTechnique(character, technique, mastery = 'Learned')
                db.session.add(ct)
            elif k == 'mastered_technique':
                technique = Technique.get(v)
                ct = CharacterTechnique(character, technique, mastery = 'Mastered')
                db.session.add(ct)
            else:
                character.set(k, v)
        db.session.commit()
        logger.debug(f'Updated {character.id}')
        step += 1
        if step == 5:
            return redirect(url_for('home')) # can eventually go to character sheet
        else:
            return redirect(url_for('edit_character', character_id = character.id, step = step)) 
    return render_template('character_edit_{}.html'.format(step), character = character, data = data)

@app.route('/api/character/<character_id>', methods = ['GET'])
def get_character(character_id):
    ''' docstring '''
    logger.debug(f'Call to get_character for {character_id}')
    data = Character.get(character_id).to_dict()
    resp = {'status': 'success', 'data': data}
    logger.debug(f'Returned {data}')
    return json.dumps(resp)

@app.route('/api/character/<character_id>', methods = ['POST']) 
def update_character(character_id):
    ''' ZZ docstring '''
    logger.debug(f'Call to update_character for {character_id}')
    character = Character.get(character_id)
    if not character:
        return json.dumps({'status': 'failure', 'message': 'That character does not exist'})
    for k, v in request.args.items():
        if k == 'playbook':
            playbook = Playbook.get_name(v)
            character.playbook_id = playbook.id
        elif k not in character.mutable_columns:
            return json.dumps({'status': 'failure', 'message': 'Invalid argument: {}'.format(k)})
        else:
            character.set(k, v)
    db.session.commit()
    logger.debug('Character updated')
    return get_character(character_id)

@app.route('/api/playbook', methods = ['GET'])
def get_playbooks():
    logger.debug('Call to get_playbooks')
    playbooks = Playbook.get_all()
    data = [p.to_dict() for p in playbooks]
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/playbook/<playbook_id>', methods = ['GET'])
def get_playbook(playbook_id):
    ''' docstring '''
    logger.debug('Call to get_playbook')
    playbook = Playbook.get(playbook_id)
    data = playbook.to_dict()
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/technique', methods = ['GET'])
def get_techniques():
    ''' docstring '''
    logger.debug('Call to get_techniques')
    techniques = Technique.get_all()
    data = [t.to_dict() for t in techniques]
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)  

@app.route('/api/technique/<technique_id>', methods = ['GET'])
def get_technique(technique_id):  
    logger.debug('Call to get_technique {technique_id}')
    technique = Technique.get(technique_id)
    data = technique.to_dict()
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/move', methods = ['GET'])
def get_moves():
    ''' docstring '''
    logger.debug('Call to get_moves')
    moves = Move.get_all()
    data = [m.to_dict() for m in moves]
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/move/<move_id>', methods = ['GET'])
def get_move(move_id):
    ''' docstring '''
    logger.debug('Call to get_move {move_id}')
    move = Move.get(move_id)
    data = move.to_dict()
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/character/<character_id>/moves', methods = ['GET'])
def get_character_moves(character_id):
    ''' docstring '''
    logger.debug('Call to get_character_moves')
    character = Character.get(character_id)
    data = [m.to_dict() for m in character.moves]
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/character/<character_id>/moves', methods = ['POST'])
def add_character_move(character_id):
    ''' docstring '''
    logger.debug('Call to add_character_move')
    move_id = request.args.get('id')
    cm = CharacterMove.get(character_id, move_id)
    if not cm: 
        character = Character.get(character_id)
        move = Move.get(m_id)
        cm = CharacterMove(character, move)
        db.session.add(cm)
        db.session.commit()
        resp = {'status': 'success', 'data': {}}
    else:
        resp = {'status': 'failure', 'message': 'Move already associated with character'}
    logger.debug(f'Inserted {move_id} for {character_id}')
    return json.dumps(resp)

@app.route('/api/character/<character_id>/techniques', methods = ['GET'])
def get_character_techniques(character_id):
    ''' docstring '''
    logger.debug('Call to get_character_techniques')
    character = Character.get(character_id)
    data = [t.to_dict() for t in character.techniques]
    resp = {'status': 'success', 'data': data}
    return json.dumps(resp)

@app.route('/api/character/<character_id>/techniques', methods = ['POST'])
def add_character_technique(character_id):
    ''' docstring '''
    logger.debug('Call to add_character_technique')
    technique_id = request.args.get('id')
    mastery = request.args.get('mastery')
    if not mastery:
        mastery = 'Learned'
    ct = CharacterTechnique.get(character_id, technique_id)
    if not ct:
        character = Character.get(character_id)
        technique = Technique.get(t_id)
        ct = CharacterTechnique(character, technique)
    else:
        # enforce Learned -> Practiced -> Mastered?
        ct.mastery = mastery
    db.session.add(ct)
    db.session.commit()
    resp = {'status': 'success', 'data': {}}
    logger.debug(f'{character_id} has learned {technique_id}')
    return json.dumps(resp)
