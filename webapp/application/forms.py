#!/usr/bin/env python

from flask import flash
from wtforms import Form, BooleanField, StringField, PasswordField, validators

def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(error)

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