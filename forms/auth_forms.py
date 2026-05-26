from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
# Importujemo EmailField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from models import User
import re


def validate_password_strength(form, field):
    """
    Custom validator for password complexity.
    Requires: at least 8 chars, 1 uppercase, 1 lowercase, 1 number
    """
    password = field.data
    if len(password) < 8:
        raise ValidationError('Lozinka mora imati najmanje 8 karaktera.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Lozinka mora sadržati najmanje jedno veliko slovo.')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Lozinka mora sadržati najmanje jedno malo slovo.')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Lozinka mora sadržati najmanje jedan broj.')

class RegistrationForm(FlaskForm):
    username = StringField('Korisničko ime', validators=[
        DataRequired(),
        Length(min=3, max=64),
        Regexp('^[A-Za-z0-9_-]+$', message='Korisničko ime može sadržati samo slova, brojeve, _ i -')
    ])
    # Koristimo EmailField umjesto StringField
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Lozinka', validators=[
        DataRequired(),
        Length(min=8, message='Lozinka mora imati najmanje 8 karaktera'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Potvrdite Lozinku', validators=[
        DataRequired(),
        EqualTo('password', message='Lozinke se moraju podudarati.')
    ])
    subscribe = BooleanField('Prijavite me na newsletter')
    submit = SubmitField('Registruj se')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Registracija nije moguća sa unesenim podacima.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Registracija nije moguća sa unesenim podacima.')

class LoginForm(FlaskForm):
    # Koristimo EmailField umjesto StringField
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ProfileForm(FlaskForm):
    first_name = StringField('Ime', validators=[Length(max=64)])
    last_name = StringField('Prezime', validators=[Length(max=64)])
    address = StringField('Adresa', validators=[Length(max=200)])
    city = StringField('Grad', validators=[Length(max=64)])
    postal_code = StringField('Poštanski broj', validators=[
        Length(max=20),
        Regexp(r'^[A-Za-z0-9\s-]+$', message='Nevažeći format poštanskog broja')
    ])
    country = StringField('Država', validators=[Length(max=64)])
    phone_number = StringField('Broj telefona', validators=[
        Length(max=20),
        Regexp(r'^\+?[0-9\s()-]+$', message='Nevažeći format broja telefona')
    ])
    is_subscribed = BooleanField('Prijavljen na newsletter')
    submit = SubmitField('Ažuriraj')