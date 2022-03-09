-- Avatar Legends: RPG Database Schema
CREATE DATABASE avatar;
USE avatar;

-- Playbooks
CREATE TABLE playbooks (
    playbook_id                     CHAR(32), -- creating a hash for everything to avoid url-masking raw names
    playbook                        VARCHAR(100),
    playbook_description            VARCHAR(1024),
    playbook_start_creativity       SMALLINT,
    playbook_start_focus            SMALLINT,
    playbook_start_harmony          SMALLINT,
    playbook_start_passion          SMALLINT,
    playbook_principle_1            VARCHAR(30),
    playbook_principle_2            VARCHAR(30),
    playbook_demeanor_options       VARCHAR(255),
    playbook_history_questions      JSON,
    playbook_connections            JSON,
    playbook_moment_of_balance      VARCHAR(1024),
    playbook_growth_question        VARCHAR(255),
    PRIMARY KEY(playbook_id)
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
    player_id                       CHAR(32) NOT NULL,
    player_name                     VARCHAR(255) NOT NULL,
    player_password_hash            CHAR(32) NOT NULL,
    player_created_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    player_updated_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(player_id)
)
;

-- Characters 
CREATE TABLE characters (
    player_id                       CHAR(32) NOT NULL,
    character_id                    CHAR(32) NOT NULL,
    character_name                  VARCHAR(255) NOT NULL,
    character_playbook_id           CHAR(32), 
    character_playbook              VARCHAR(30), 
    character_training              VARCHAR(50),
    character_fighting_style        VARCHAR(255),
    character_background            VARCHAR(50),
    character_hometown              VARCHAR(255),
    character_hometown_nation       ENUM('Water','Air','Fire','Earth'),
    character_demeanors             VARCHAR(255),
    character_appearance            VARCHAR(1024),
    character_history_questions     JSON,
    character_connections           JSON,
    character_creativity            SMALLINT,
    character_focus                 SMALLINT,
    character_harmony               SMALLINT,
    character_passion               SMALLINT,
    character_fatigue               SMALLINT DEFAULT 0, -- possibly move to secondary table to track temporary conditions
    character_balance               SMALLINT DEFAULT 0, -- possibly move to secondary table to track temporary conditions
    character_balance_center        SMALLINT DEFAULT 0,
    character_growth                SMALLINT DEFAULT 0,
    character_growth_advancements   SMALLINT DEFAULT 0,
    character_mob_unlocked          BOOLEAN DEFAULT FALSE, -- "mob" = moment of balance
    character_created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    character_updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(character_id),
    FOREIGN KEY(player_id) REFERENCES players (player_id) ON DELETE CASCADE
)
;

-- Character Moves
CREATE TABLE character_moves (
    character_id                    CHAR(32),
    move_id                         CHAR(32),
    FOREIGN KEY(character_id) REFERENCES characters (character_id) ON DELETE CASCADE,
    FOREIGN KEY(move_id) REFERENCES moves (move_id) ON DELETE CASCADE
)
;

CREATE TABLE character_techniques (
    character_id                    CHAR(32),
    technique_id                    CHAR(32),
    technique_mastery               ENUM('Basic','Learned','Practiced','Mastered'),
    FOREIGN KEY(character_id) REFERENCES characters (character_id) ON DELETE CASCADE,
    FOREIGN KEY(technique_id) REFERENCES techniques (technique_id) ON DELETE CASCADE
)

;

-- Character Conditions

-- Character Statuses