#!/usr/bin/env python

import json
from datetime import datetime
from hashlib import md5

from . import db

# temp defs for enums. https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.Enum
backgrounds = ['Military','Monastic','Outlaw','Privileged','Urban','Wilderness']
nations = ['Water','Air','Fire','Earth']
trainings = ['Waterbending','Airbending','Firebending','Earthbending','Weapons','Technology']

class DbMixIn(object):
    ''' Base class for project database models '''

    protected_columns_ = []

    @classmethod
    def get(cls, id):
        return cls.query.filter_by(id = id).first()

    @classmethod
    def get_name(cls, name):
        return cls.query.filter_by(name = name).first()

    def columns(self, writeable = True):
        cols = [c.key for c in self.__table__.columns if c.key not in self.protected_columns_ and writeable == True]
        return cols

    def to_json(self):
        d = {}
        for col in self.columns(writeable = False):
            d.update({col: self.__getattr__(col)})
        return json.dumps(d)

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
    created_at = db.Column(db.DateTime, default = datetime.utcnow())
    updated_at = db.Column(db.DateTime, default = datetime.utcnow())

    player = db.relationship('Player', back_populates = 'characters', uselist = False)
    playbook = db.relationship('Playbook', viewonly = True, uselist = False)

    protected_columns_ = ['player_id','id','name']
    
    def set(self, attr, value):
        self.__setattr__(attr, value)

    def get_name(player_id, name):
        return Character.query.filter_by(name = name, player_id = player_id).first()

    def __init__(self, player, name, **kwargs):
        super(Character, self).__init__(**kwargs)
        self.player_id = player.id # change to get_id()
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
    created_at = db.Column(db.DateTime, default = datetime.utcnow())
    updated_at = db.Column(db.DateTime, default = datetime.utcnow())

    characters = db.relationship('Character', back_populates = 'player')

    protected_columns_ = ['id','name','created_at']

    def __init__(self, name, password, **kwargs):
        super(Player, self).__init__(**kwargs)
        self.name = name
        self.id = md5(self.name.encode()).hexdigest()
        self.password_hash = md5(password.encode()).hexdigest()






