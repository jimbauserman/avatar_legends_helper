#!/usr/bin/env python

import os
import json
import logging
from datetime import datetime
from hashlib import md5
from flask import request, render_template, url_for, flash, redirect, abort
from flask_login import current_user, login_user, logout_user, login_required
from is_safe_url import is_safe_url

from . import app, db, login_manager
from .db_model import *
from .forms import RegistrationForm, LoginForm, CharacterCreateForm, CharacterEditForm, flash_errors

FLASK_APP_HOST = os.environ['FLASK_APP_HOST']

logger = logging.getLogger('routes')

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
    logger.debug('Request to register')
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        player_name = form.name.data 
        logger.debug(f'Call to create_player for {player_name}')
        if Player.get_name(player_name):
            flash('''Player name {name} already exists. <a href="{url}">Login here.</a>'''.format(name = player_name, url = url_for('login')), 'danger')
        else:
            player = Player(player_name, form.password.data)
            db.session.add(player)
            db.session.commit()
            logger.debug(f'Inserted {player.id}')
            login_user(player)
            return redirect(url_for('home'))
    else:
        flash_errors(form)
    return render_template('register.html', form = form)

@app.route('/login', methods = ['GET','POST'])
def login():
    logger.debug('Request to login')
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        player_name = form.name.data 
        logger.debug('Login for {player_name} submitted')
        req_pw = md5(form.password.data.encode()).hexdigest()
        player = Player.get_name(player_name)
        if not player:
            flash('''No player with that name exists. <a href="{url}">Sign up here!</a>'''.format(url = url_for('register')), 'danger')
        else:
            if req_pw != player.password_hash:
                flash('Incorrect player name or password', 'danger')
                logger.debug('Failed attempt')
            else:
                logger.debug('Successful attempt')
                login_user(player)
                # handle if user was redirected to login
                next = request.args.get('next')
                if next and not is_safe_url(next, {FLASK_APP_HOST}):
                    return abort(400)
                return redirect(next or url_for('home'))
    else:
        flash_errors(form)

    return render_template('login.html', form = form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/character')
def character():
    pass

@app.route('/character/create', methods = ['GET','POST'])
@login_required
def create_character():
    ''' ZZ docstring '''
    logger.debug('Call to create_character')
    player = current_user
    form = CharacterCreateForm(request.form)
    form.playbook_id.choices = [(p.id, p.name) for p in Playbook.get_all()]
    if request.method == 'POST' and form.validate():
        character_name = form.name.data
        character = Character.get_name(player.id, character_name)
        if character:
            flash('You already have a character with that name', 'danger')
        else:
            playbook_id = form.playbook_id.data
            character = Character(player, character_name, playbook_id)
            db.session.add(character)
            for move in Move.starting_moves():
                cm = CharacterMove(character.id, move.id)
                db.session.add(cm)
            for technique in Technique.starting_techniques():
                ct = CharacterTechnique(character.id, technique.id)
                db.session.add(ct)
            db.session.commit()
            for s in statistics:
                character.set(s.lower(), character.playbook.stats[s])
            db.session.commit()
            logger.debug(f'{character.name} created')
            return redirect(url_for('edit_character', character_id = character.id))
    else:
        flash_errors(form)
    return render_template('character_create.html', form = form)

@app.route('/character/<character_id>/edit', methods = ['GET','POST']) 
@login_required # doesnt check if character actually belongs to logged in player
def edit_character(character_id):
    ''' ZZ docstring '''
    logger.debug('Call to edit_character')
    character = Character.get(character_id)
    form = CharacterEditForm(request.form)
    form.set_choices(character) # technique choices always lagged by one submit 
    if request.method == 'GET':
        form.set_defaults(character)
    elif request.method == 'POST' and form.validate():
        for field, value in form.data.items():
            if value and any(value):
                # all this junk should probably be methods of Character
                if field == 'stat':
                    prev = character.creation_stat_increase
                    if not prev:
                        character.creation_stat_increase = value # there has to be a way to not repeat these two lines
                        character.set(value.lower(), character.stats[value] + 1)
                    elif prev != value: 
                        character.set(prev.lower(), character.stats[prev] - 1)
                        character.creation_stat_increase = value
                        character.set(value.lower(), character.stats[value] + 1)
                    # else remained the same so do nothing
                elif field == 'moves':
                    if character.creation_moves:
                        new = [m for m in value if m not in character.creation_moves]
                        removed = [m for m in character.creation_moves if m not in value]
                    else:
                        new = value 
                        removed = []
                    for move_id in new:
                        cm = CharacterMove(character.id, move_id)
                        db.session.add(cm)
                    for move_id in removed:
                        cm = CharacterMove.get(character.id, move_id)
                        db.session.delete(cm)
                    character.creation_moves = value
                elif field == 'techniques':
                    dict_value = {'Learned': value[0], 'Mastered': value[1]}
                    if character.creation_techniques:
                        prev_l = character.creation_techniques['Learned']
                        prev_m = character.creation_techniques['Mastered']
                        if dict_value['Learned'] != prev_l:
                            del_ct = CharacterTechnique.get(character.id, prev_l)
                            db.session.delete(del_ct)
                        if dict_value['Mastered'] != prev_m:
                            del_ct = CharacterTechnique.get(character.id, prev_m)
                            db.session.delete(del_ct)   
                    character.creation_techniques = dict_value
                    ctl = CharacterTechnique(character_id, dict_value['Learned'], mastery = 'Learned')
                    ctm = CharacterTechnique(character_id, dict_value['Mastered'], mastery = 'Mastered')
                    db.session.add(ctl)
                    db.session.add(ctm)
                else:
                    character.set(field, value)
        db.session.commit()
        logger.debug(f'Updated {character.id}')
        flash('Character updated', 'success') 
        # return redirect(url_for('home')) # can eventually go to character sheet
    else:
        flash_errors(form)
    return render_template('character_edit.html', character = character, form = form) # would be nice if this snapped you back to tab you were on

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
