#!/usr/bin/env python

import json
import logging
from datetime import datetime
from hashlib import md5
from sqlalchemy.ext.associationproxy import association_proxy

from . import db

logger = logging.getLogger('db_model')

# temp defs for enums. https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.Enum
backgrounds = ['Military','Monastic','Outlaw','Privileged','Urban','Wilderness']
nations = ['Water','Air','Fire','Earth']
trainings = ['Waterbending','Airbending','Firebending','Earthbending','Weapons','Technology']
move_types = ['Basic','Balance','Playbook','Advancement','Custom']
statistics = ['Creativity','Focus','Harmony','Passion']
approaches = ['Defend and Maneuver','Advance and Attack','Evade and Observe']

class DbMixIn(object):
    ''' Base class for project database models '''

    protected_columns_ = []

    @classmethod
    def get(cls, id): # this is apparently implemented natively?
        return cls.query.filter_by(id = id).first()

    @classmethod
    def get_or_404(cls, id):
        return cls.query.filter_by(id = id).first_or_404()

    @classmethod
    def get_name(cls, name): # might want to construct an index on name fields if this is used a lot
        return cls.query.filter_by(name = name).first()

    def columns(self, writeable = True):
        cols = [c.key for c in self.__table__.columns if c.key not in self.protected_columns_ or writeable == False]
        return cols

    def to_dict(self, extra_attrs = []):
        return {col: self.__dict__[col] for col in self.columns(writeable = False) + extra_attrs}

    def __init__(self, **kwargs):
        super(DbMixIn, self).__init__(**kwargs)

class Playbook(db.Model, DbMixIn):
    '''
    CREATE TABLE playbooks (
        id                     CHAR(32), 
        name                   VARCHAR(100),
        description            VARCHAR(1024),
        start_creativity       SMALLINT,
        start_focus            SMALLINT,
        start_harmony          SMALLINT,
        start_passion          SMALLINT,
        principle_1            VARCHAR(30),
        principle_2            VARCHAR(30),
        demeanor_options       VARCHAR(255),
        history_questions      VARCHAR(1024),
        connections            VARCHAR(1024),
        moment_of_balance      VARCHAR(1024),
        growth_question        VARCHAR(255),
        PRIMARY KEY(id)
    )
    ;
    '''
    __tablename__ = 'playbooks'
    id = db.Column(db.String(32), primary_key = True, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    start_creativity = db.Column(db.SmallInteger)
    start_focus = db.Column(db.SmallInteger)
    start_harmony = db.Column(db.SmallInteger)
    start_passion = db.Column(db.SmallInteger)
    principle_1 = db.Column(db.String(30))
    principle_2 = db.Column(db.String(30))
    demeanor_options = db.Column(db.String(255))
    history_questions = db.Column(db.String(1024))
    connections = db.Column(db.String(1024))
    moment_of_balance = db.Column(db.String(1024))
    growth_question = db.Column(db.String(255))

    protected_columns_ = ['id','name','start_creativity','start_focus','start_harmony',
                        'start_passion','principle_1','principle_2','history_questions',
                        'connections','moment_of_balance','growth_question']

    def __init__(self, **kwargs):
        super(Playbook, self).__init__(**kwargs)

class Move(db.Model, DbMixIn):
    '''
    CREATE TABLE moves ( -- need to redo this. does not fit balance moves
        id                              CHAR(32),
        name                            VARCHAR(100),
        move_type                       ENUM('Basic','Balance','Playbook','Advancement','Custom'),
        playbook                        VARCHAR(100),
        statistic                       ENUM('Creativity','Focus','Harmony','Passion'),
        description                     VARCHAR(1024),
        miss_outcome                    VARCHAR(255),
        weak_hit_outcome                VARCHAR(255),
        strong_hit_outcome              VARCHAR(255),
        PRIMARY KEY(id)
    )
    ;
    '''
    __tablename__ = 'moves'
    id = db.Column(db.String(32), primary_key = True, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    move_type = db.Column(db.Enum(*move_types))
    playbook = db.Column(db.String(100)) # should be tied to playbook table
    statistic = db.Column(db.Enum(*statistics), nullable = True)
    description = db.Column(db.String(1024))
    miss_outcome = db.Column(db.String(255))
    weak_hit_outcome = db.Column(db.String(255))
    strong_hit_outcome = db.Column(db.String(255))

    protected_columns_ = ['id','name','move_type','playbook','statistic',
                        'description','miss_outcome','weak_hit_outcome','strong_hit_outcome']

    def starting_moves():
        return Move.query.filter(Move.move_type.in_(['Basic','Balance','Advancement'])).all()

    def __init__(self, **kwargs):
        super(Move, self).__init__(**kwargs)

class Technique(db.Model, DbMixIn):
    '''
    CREATE TABLE techniques (
        id                              CHAR(32),
        name                            VARCHAR(100),
        technique_type                  ENUM('Basic','Advanced'),
        approach                        ENUM('Defend and Maneuver','Advance and Attack','Evade and Observe'),
        req_training                    ENUM('Universal','Waterbending','Airbending','Firebending','Earthbending','Weapons','Technology'),
        req_playbook                    VARCHAR(100),
        description                     VARCHAR(1024),
        cost                            VARCHAR(100),
        fatigue_cleared                 SMALLINT,
        conditions_cleared              VARCHAR(100),
        fatigue_inflicted               SMALLINT,
        conditions_inflicted            VARCHAR(100), -- add statuses cleared and inflicted
        is_blockable                    BOOLEAN,
        is_rare                         BOOLEAN,
        PRIMARY KEY(id)
    )
    ;
    '''
    __tablename__ = 'techniques'
    id = db.Column(db.String(32), primary_key = True, nullable = False)
    name = db.Column(db.String(100), nullable = False)
    technique_type = db.Column(db.Enum(*['Basic','Advanced']))
    approach = db.Column(db.Enum(*approaches))
    req_training = db.Column(db.Enum(*['Universal']+trainings)) # should be tied to non-existent trainings table?
    req_playbook = db.Column(db.String(100)) # should be tied to playbook table?
    description = db.Column(db.String(1024))
    cost = db.Column(db.String(100))
    fatigue_cleared = db.Column(db.SmallInteger)
    conditions_cleared = db.Column(db.String(100))
    fatigue_inflicted = db.Column(db.SmallInteger)
    conditions_inflicted = db.Column(db.String(100))
    is_blockable = db.Column(db.Boolean)
    is_rare = db.Column(db.Boolean)

    # want technique to also return its mastery level when queried as part of Character.techniques
    # https://docs.sqlalchemy.org/en/14/orm/extensions/associationproxy.html#sqlalchemy.ext.associationproxy.association_proxy
    # when trying to reference below attribute as 'mastery' or 'technique_mastery' get KeyError
    # mastery = association_proxy('technique_mastery', 'character_mastery')

    protected_columns_ = ['id','name','technique_type','approach','req_training','req_playbook',
                        'description','cost','fatigue_cleared','conditions_cleared',
                        'fatigue_inflicted','conditions_inflicted','is_blockable','is_rare']

    def starting_techniques():
        return Technique.query.filter(Technique.technique_type == 'Basic').all()

    def __init__(self, **kwargs):
        super(Technique, self).__init__(**kwargs)

class Character(db.Model, DbMixIn):
    '''
    CREATE TABLE characters (
        player_id                       CHAR(32) NOT NULL,
        id                              CHAR(32) NOT NULL,
        name                            VARCHAR(255) NOT NULL,
        playbook_id                     CHAR(32), 
        playbook_name                   VARCHAR(100), 
        training                        VARCHAR(50),
        fighting_style                  VARCHAR(255),
        background                      VARCHAR(50),
        hometown                        VARCHAR(255),
        hometown_nation                 ENUM('Water','Air','Fire','Earth'),
        demeanors                       VARCHAR(255),
        appearance                      VARCHAR(1024),
        history_questions               VARCHAR(1024),
        connections                     VARCHAR(1024),
        creativity                      SMALLINT,
        focus                           SMALLINT,
        harmony                         SMALLINT,
        passion                         SMALLINT,
        fatigue                         SMALLINT DEFAULT 0, 
        balance                         SMALLINT DEFAULT 0, 
        balance_center                  SMALLINT DEFAULT 0,
        growth                          SMALLINT DEFAULT 0,
        growth_advancements             SMALLINT DEFAULT 0,
        mob_unlocked                    BOOLEAN DEFAULT FALSE, -- "mob" = moment of balance
        created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(id),
        FOREIGN KEY(player_id) REFERENCES player (id) ON DELETE CASCADE,
        FOREIGN KEY(playbook_id) REFERENCES playbook (id)
    )
    ;
    '''
    __tablename__ = 'characters'
    player_id = db.Column(db.String(32), db.ForeignKey('players.id'), nullable = False)
    id = db.Column(db.String(32), primary_key = True, nullable = False)
    name = db.Column(db.String(255), nullable = False)
    playbook_id = db.Column(db.String(32), db.ForeignKey('playbooks.id')) # eventually needs to support characters changing playbooks
    # playbook_name = db.relationship('Playbook', backref = db.backref('name', lazy = True))
    training = db.Column(db.String(50)) # will eventually need to ref training table
    fighting_style = db.Column(db.String(255))
    background = db.Column(db.Enum(*backgrounds))
    hometown = db.Column(db.String(255))
    hometown_nation = db.Column(db.Enum(*nations))
    demeanors = db.Column(db.String(255))
    appearance = db.Column(db.String(1024))
    history_questions = db.Column(db.String(1024))
    connections = db.Column(db.String(1024))
    creativity = db.Column(db.SmallInteger)
    focus = db.Column(db.SmallInteger)
    harmony = db.Column(db.SmallInteger)
    passion = db.Column(db.SmallInteger)
    fatigue = db.Column(db.SmallInteger, default = 0)
    balance = db.Column(db.SmallInteger, default = 0)
    balance_center = db.Column(db.SmallInteger, default = 0)
    growth = db.Column(db.SmallInteger, default = 0)
    growth_advancements = db.Column(db.SmallInteger, default = 0)
    mob_unlocked = db.Column(db.Boolean, default = False)
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate = datetime.utcnow)

    player = db.relationship('Player', back_populates = 'characters', uselist = False)
    playbook = db.relationship('Playbook', viewonly = True, uselist = False)
    moves = db.relationship('Move', secondary = lambda: CharacterMove.__table__, viewonly = True)
    techniques = db.relationship('Technique', secondary = lambda: CharacterTechnique.__table__, viewonly = True)

    protected_columns_ = ['player_id','id','name']
    
    def set(self, attr, value):
        self.__setattr__(attr, value)

    def get_name(player_id, name):
        return Character.query.filter_by(name = name, player_id = player_id).first()

    def __init__(self, player, name, **kwargs):
        super(Character, self).__init__(**kwargs)
        self.player_id = player.id 
        self.name = name
        self.id = md5((self.player_id + self.name).encode()).hexdigest()

class Player(db.Model, DbMixIn):
    '''
    CREATE TABLE players (
        id                              CHAR(32) NOT NULL,
        name                            VARCHAR(255) NOT NULL,
        password_hash                   CHAR(32) NOT NULL,
        created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(id)
    )
    ;
    '''
    __tablename__ = 'players'
    id = db.Column(db.String(32), primary_key = True, nullable = False)
    name = db.Column(db.String(255), nullable = False)
    password_hash = db.Column(db.String(32), nullable = False)
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate = datetime.utcnow)

    characters = db.relationship('Character', back_populates = 'player')

    protected_columns_ = ['id','name','created_at']

    def __init__(self, name, password, **kwargs):
        super(Player, self).__init__(**kwargs)
        self.name = name
        self.id = md5(self.name.encode()).hexdigest()
        self.password_hash = md5(password.encode()).hexdigest()

class CharacterMove(db.Model):
    '''
    CREATE TABLE character_moves (
        character_id                    CHAR(32) NOT NULL,
        move_id                         CHAR(32) NOT NULL,
        FOREIGN KEY(character_id) REFERENCES characters (id) ON DELETE CASCADE,
        FOREIGN KEY(move_id) REFERENCES moves (id) ON DELETE CASCADE
    )
    ;
    '''
    __tablename__ = 'character_moves'
    character_id = db.Column(db.String(32), db.ForeignKey('characters.id'), primary_key = True, nullable = False)
    move_id = db.Column(db.String(32), db.ForeignKey('moves.id'), primary_key = True, nullable = False)

    def __init__(self, character, move, **kwargs):
        super(CharacterMove, self).__init__(**kwargs)
        self.character_id = character.id 
        self.move_id = move.id

class CharacterTechnique(db.Model):
    '''
    CREATE TABLE character_techniques (
        character_id                    CHAR(32),
        technique_id                    CHAR(32),
        mastery                         ENUM('Basic','Learned','Practiced','Mastered'),
        FOREIGN KEY(character_id) REFERENCES characters (id) ON DELETE CASCADE,
        FOREIGN KEY(technique_id) REFERENCES techniques (id) ON DELETE CASCADE
    )
    ;
    '''
    __tablename__ = 'character_techniques'
    character_id = db.Column(db.String(32), db.ForeignKey('characters.id'), primary_key = True, nullable = False)
    technique_id = db.Column(db.String(32), db.ForeignKey('techniques.id'), primary_key = True, nullable = False)
    mastery = db.Column(db.Enum(*['Basic','Learned','Practiced','Mastered']))

    # character_mastery = db.relationship('Technique', backref = db.backref('technique_mastery'))

    def __init__(self, character, technique, mastery = None, **kwargs):
        super(CharacterTechnique, self).__init__(**kwargs)
        self.character_id = character.id 
        self.technique_id = technique.id
        if not mastery:
            self.mastery = 'Basic' if technique.technique_type == 'Basic' else 'Learned'
        else:
            self.mastery = mastery



