#!/usr/bin/env python

import logging
from flask import flash
from wtforms import Form, validators
from wtforms.fields import StringField, PasswordField, SelectField, RadioField, TextAreaField, SelectMultipleField, FieldList, FormField
from wtforms.widgets import ListWidget, CheckboxInput

from .db_model import statistics, trainings, backgrounds, nations

logger = logging.getLogger('forms')

def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')

# Custom validators
class FieldListOptional(object):
    def __init__(self, check_if_any = True):
        if check_if_any:
            self.is_populated = lambda x: any(x)
        else:
            self.is_populated = lambda x: all(x)
        self.field_flags = {"optional": True}

    def __call__(self, form, field):
        if not self.is_populated(field.data):
            field.errors[:] = []
            raise validators.StopValidation()

class FieldListLength(object):
    def __init__(self, min=-1, max=-1, message=None):
        self.min = min
        self.max = max
        if not message:
            message = 'Field must be between %i and %i entries long.' % (min, max)
        self.message = message

    def __call__(self, form, field):
        logger.debug('Called FieldListLength')
        l = 0
        if field.data:
            nonnull_data = [x for x in field.data if x]
            logger.debug(f'nonnull_data {nonnull_data}')
            l = len(nonnull_data)
            logger.debug(f'l {l}')
        if l < self.min or self.max != -1 and l > self.max:
            raise validators.ValidationError(self.message)

class FieldListNotEqual(object):
    def __init__(self, message = None):
        if not message:
            message = 'Please select different options for {l1} and {l2}'
        self.message = message

    def __call__(self, form, field):
        for e1 in field.entries:
            for e2 in field.entries:
                if e1.label != e2.label and e1.data == e2.data:
                    try:
                        message = self.message.format(l1 = e1.label, l2 = e2.label)
                    except KeyError:
                        message = self.message
                    raise validators.ValidationError(message)

# Custom fields
class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

# Forms
class RegistrationForm(Form):
    name = StringField('Player Name', [
        validators.Length(min = 4, max = 25, message = 'Player name must be between 4 and 25 characters long')
    ])
    password = PasswordField('New Password', [
        validators.DataRequired(message = 'Please enter a password'),
        validators.EqualTo('confirm', message = 'Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')

class LoginForm(Form):
    name = StringField('Player Name', [
        validators.Length(min = 4, max = 25, message = 'Player name must be between 4 and 25 characters long')
    ])
    password = PasswordField('Password', [
        validators.DataRequired(message = 'Please enter a password')
    ])

class CharacterCreateForm(Form):
    name = StringField('Character Name', [
        validators.DataRequired(message = 'Please enter a name for your character'),
        validators.Length(max = 100, message = 'Character name can be no more than 100 characters long')
    ])
    playbook_id = RadioField(
        'Playbook', 
        [validators.DataRequired(message = 'Please select a playbook before continuing')]
    )

class CharacterTechniqueForm(Form):
    learned = RadioField('Learned', [validators.Optional()])
    mastered = RadioField('Mastered', [validators.Optional()])

class CharacterEditForm(Form):

    creation_stat_increase = RadioField(
        'Choose one statistic to increase by +1', 
        [validators.Optional()]
    )
    training = RadioField(
        "Select your character's training", 
        [validators.Optional()], 
        choices = trainings
    )
    fighting_style = TextAreaField(
        "Describe your character's fighting style",
        [validators.Optional(), validators.Length(max = 255, message = 'Fighting Style can be no more than 255 characters')]
    )
    background = RadioField(
        "Select your character's background",
        [validators.Optional()],
        choices = backgrounds
    )
    hometown = StringField(
        'Where is your character from?',
        [validators.Optional(), validators.Length(max = 255, message = 'Hometown can be no more than 255 characters')]
    )
    hometown_region = RadioField(
        'In which region?', 
        [validators.Optional()],
        choices = nations
    )
    appearance = StringField(
        'What does your character look like?',
        [validators.Optional(), validators.Length(max = 255, message = 'Appearance can be no more than 1024 characters')]
    )
    demeanors = MultiCheckboxField(
        "What is your character's demeanor? (Select 2)",
        [validators.Optional(), validators.Length(min = 2, max = 2, message = 'Please select exactly two demeanors')]
    )
    history_questions = FieldList(
        StringField('placeholder', [validators.Optional()]),
        'Character History', 
        min_entries = 5
    )
    connections = FieldList(
        StringField('placeholder', [validators.Optional()]), 
        'Character Connections', 
        min_entries = 2
    )
    creation_moves = MultiCheckboxField(
        "Select two moves from your character's playbook",
        [validators.Optional(), validators.Length(min = 2, max = 2, message = 'Please select exactly two moves')]
    )
    creation_techniques = FieldList(
        RadioField('placeholder', [validators.Optional()]),
        'Select one learned and one mastered technique',
        [FieldListOptional(), FieldListNotEqual(), FieldListLength(min = 2, max = 2, message = 'Please select one technique of each type')],
        min_entries = 2, max_entries = 2
    )

    def set_choices(self, character):
        base_stats = character.playbook.str_stats
        self.creation_stat_increase.choices = [(s, '{} (base: {})'.format(s, base_stats[s])) for s in statistics]
        self.demeanors.choices = character.playbook.demeanor_options
        self.creation_moves.choices = [(m.id, m.name + ': ' + m.description) for m in character.playbook.moves]
        for i, e in enumerate(self.history_questions.entries):
            e.label = character.playbook.history_questions[i]
        for i, e in enumerate(self.connections.entries):
            e.label = character.playbook.connections[i].replace('$BLANK$', '_'*10)
        t_list = character.available_techniques(include_known = True)
        for i, e in enumerate(self.creation_techniques.entries):
            e.label = 'Learned' if i == 0 else 'Mastered'
            e.choices = [(t.id, t.name + ': ' + t.description) for t in t_list]
        t_lbl = 'Select one learned and one mastered technique'
        t_lbl_add = '(Select a training to see additional options)'
        self.creation_techniques.label = t_lbl if character.training else ' '.join([t_lbl, t_lbl_add])

    def set_defaults(self, character):
        self.creation_stat_increase.data = character.creation_stat_increase
        self.training.data = character.training
        self.fighting_style.data = character.fighting_style
        self.background.data = character.background
        self.hometown.data = character.hometown
        self.hometown_region.data = character.hometown_region
        self.appearance.data = character.appearance
        self.demeanors.data = character.demeanors
        self.creation_moves.data = character.creation_moves
        for i, e in enumerate(self.history_questions.entries):
            e.data = character.history_questions[i] if character.history_questions else None
        for i, e in enumerate(self.connections.entries):
            e.data = character.connections[i] if character.connections else None
        for i, e in enumerate(self.creation_techniques.entries):
            mastery = 'Learned' if i == 0 else 'Mastered'
            e.data = character.creation_techniques[mastery] if character.creation_techniques else None




