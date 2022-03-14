-- Avatar Legends: RPG Database Schema
CREATE DATABASE avatar;
USE avatar;

-- Playbooks
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

-- Playbook special features, The Adamant's Lodestar

-- Trainings
CREATE TABLE trainings (
    training                        VARCHAR(30)
)
;

-- Approaches
CREATE TABLE approaches (
    approach                        VARCHAR(30),
    approach_statistic              VARCHAR(30),
    approach_fatigue_cleared        SMALLINT
)
;

-- Moves
CREATE TABLE moves ( -- need to redo this. does not fit balance moves
    move_id                         CHAR(32),
    move                            VARCHAR(100),
    move_type                       ENUM('Basic','Balance','Playbook','Advancement','Custom'),
    move_playbook                   VARCHAR(100),
    move_statistic                  ENUM('Creativity','Focus','Harmony','Passion'),
    move_description                VARCHAR(1024),
    move_miss_outcome               VARCHAR(255),
    move_weak_hit_outcome           VARCHAR(255),
    move_strong_hit_outcome         VARCHAR(255),
    PRIMARY KEY(move_id)
)
;

-- Techniques
CREATE TABLE techniques (
    technique_id                    CHAR(32),
    technique                       VARCHAR(100),
    technique_type                  ENUM('Basic','Advanced'),
    technique_approach              ENUM('Defend and Maneuver','Advance and Attack','Evade and Observe'),
    technique_req_training          ENUM('Universal','Waterbending','Airbending','Firebending','Earthbending','Weapons','Technology'),
    technique_req_playbook          VARCHAR(100),
    technique_description           VARCHAR(1024),
    technique_cost                  JSON,
    technique_fatigue_cleared       SMALLINT,
    technique_conditions_cleared    VARCHAR(100),
    technique_fatigue_inflicted     SMALLINT,
    technique_conditions_inflicted  VARCHAR(100), -- add statuses cleared and inflicted
    technique_is_blockable          BOOLEAN,
    technique_is_rare               BOOLEAN,
    PRIMARY KEY(technique_id)
)
;

-- Conditions
CREATE TABLE conditions (
    condition_id                    CHAR(32),
    condition_name                  VARCHAR(30),
    condition_penalty_move_1        VARCHAR(100), -- make these a JSON array?
    condition_penalty_move_2        VARCHAR(100),
    condition_cleared_by            VARCHAR(100),
    PRIMARY KEY(condition_id)
)
;

-- Statuses
CREATE TABLE statuses (
    status_id                       CHAR(32),
    status_name                     VARCHAR(20),
    status_is_positive              BOOLEAN,
    status_description              VARCHAR(1024),
    PRIMARY KEY(status_id)
)
;

-- Players
CREATE TABLE players (
    id                              CHAR(32) NOT NULL,
    name                            VARCHAR(255) NOT NULL,
    password_hash                   CHAR(32) NOT NULL,
    created_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id)
)
;

-- Characters 
CREATE TABLE characters (
    player_id                       CHAR(32) NOT NULL,
    id                              CHAR(32) NOT NULL,
    name                            VARCHAR(255) NOT NULL,
    playbook_id                     CHAR(32), 
    -- playbook_name                   VARCHAR(100), 
    training                        VARCHAR(50),
    fighting_style                  VARCHAR(255),
    background                      ENUM('Military','Monastic','Outlaw','Privileged','Urban','Wilderness'),
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
    FOREIGN KEY(player_id) REFERENCES players (id) ON DELETE CASCADE,
    FOREIGN KEY(playbook_id) REFERENCES playbooks (id)
)
;

-- Character Moves
CREATE TABLE character_moves (
    character_id                    CHAR(32),
    move_id                         CHAR(32),
    FOREIGN KEY(character_id) REFERENCES characters (id) ON DELETE CASCADE,
    FOREIGN KEY(move_id) REFERENCES moves (move_id) ON DELETE CASCADE
)
;

CREATE TABLE character_techniques (
    character_id                    CHAR(32),
    technique_id                    CHAR(32),
    technique_mastery               ENUM('Basic','Learned','Practiced','Mastered'),
    FOREIGN KEY(character_id) REFERENCES characters (id) ON DELETE CASCADE,
    FOREIGN KEY(technique_id) REFERENCES techniques (technique_id) ON DELETE CASCADE
)

;

-- Character Conditions

-- Character Statuses