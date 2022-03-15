#!/usr/bin/env python

import os
import json
import logging
from datetime import datetime
from hashlib import md5
from flask import Flask, request, render_template, url_for, flash, redirect

from . import app, db
from .db_model import Player, Character, Playbook, Move, CharacterMove, Technique, CharacterTechnique

logger = logging.getLogger('routes')

# need helper fns to validate request structure

@app.route('/')
def index():
    logger.debug('Request to index')
    return render_template('index.html')

@app.route('/home/<player_id>')
def home(player_id):
    logger.debug('Request to home')
    if not player_id or player_id == '':
        return redirect(url_for('index'))
    player = Player.get_or_404(player_id)
    char_data = []
    for c in player.characters:
        if not c.playbook: # we might want to require playbook on character creation
            pb = ''
        else:
            pb = c.playbook.name
        char_data.append({'id': c.id, 'name': c.name, 'playbook': pb})
    # char_data = [{'name': c.name, 'playbook': c.playbook.name} for c in player.characters]
    return render_template('home.html', name = player.name, chars = char_data)

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
            if Player.get_name(player_name):
                flash('''Player name {} already exists. <a href="{{ url_for('login') }}">Login here.</a>'''.format(player_name)) # this doesnt work
            else:
                player = Player(player_name, player_pass_raw)
                db.session.add(player)
                db.session.commit()
                logger.debug(f'Inserted {player.id}')
                return redirect(url_for('home', player_id = player.id))
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
        player = Player.get_name(player_name)
        if not player:
            flash('''No player with that name exists. <a href="{{ url_for('register') }}">Sign up here!</a>''') # this doesnt work
        else:
            logger.debug(f'db password: {player.password_hash}')
            if req_pw != player.password_hash:
                flash('Incorrect player name or password.')
                logger.debug('Failed attempt')
            else:
                logger.debug('Successful attempt')
                return redirect(url_for('home', player_id = player.id))

    return render_template('login.html')

@app.route('/character')
def character():
    pass

@app.route('/api/character/create', methods = ['POST']) 
def create_character():
    ''' ZZ docstring '''
    logger.debug('Call to create_character')
    player_id = request.args.get('user')
    player = Player.get(player_id)
    logger.debug(f'for {player_id}')
    character_name = request.args.get('cname')
    if Character.get_name(player.id, character_name):
        resp = {'status': 'failure', 'message': 'Character already exists', 'data': {}}
        logger.debug('Duplicate character found')
    else:
        player = Player.get(player_id)
        character = Character(player, character_name)
        db.session.add(character)
        for move in Move.starting_moves():
            cm = CharacterMove(character, move)
            db.session.add(cm)
        for technique in Technique.starting_techniques():
            ct = CharacterTechnique(character, technique)
            db.session.add(ct)
        db.session.commit()
        resp = {'status': 'success', 'data': {'character_id': character.id}}
        logger.debug(f'{character.name} created')
    return json.dumps(resp)

@app.route('/api/character/<character_id>', methods = ['GET'])
def get_character(character_id):
    ''' docstring '''
    logger.debug('Call to get_character for {character_id}')
    data = Character.get(character_id).to_dict()
    resp = {'status': 'success', 'data': data}
    logger.debug(f'Returned {data}')
    return json.dumps(resp)

@app.route('/api/character/<character_id>', methods = ['POST']) 
def update_character(character_id):
    ''' ZZ docstring '''
    logger.debug('Call to update_character for {character_id}')
    character = Character.get(character_id)
    if not character:
        return json.dumps({'status': 'failure', 'message': 'That character does not exist'})
    for k, v in request.args.items():
        if k == 'playbook':
            playbook = Playbook.get_name(v)
            character.playbook_id = playbook.id
        elif k not in character.columns():
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
def get_techniques(technique_id):  
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

@app.route('/api/character/moves', methods = ['POST'])
def add_character_move():
    ''' docstring '''
    logger.debug('Call to add_character_move')
    c_id = request.args.get('id')
    m_id = request.args.get('mid')
    character = Character.get(c_id)
    move = Move.get(m_id)
    cm = CharacterMove(character, move)
    db.session.add(cm)
    db.session.commit()
    resp = {'status': 'success', 'data': {}}
    logger.debug(f'Inserted {m_id} for {c_id}')
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
    logger.debug(f'{c_id} has learned {t_id}')
    return json.dumps(resp)
