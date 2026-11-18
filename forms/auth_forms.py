from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
# Importujemo EmailField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp, Optional
from models import User
import re

REQUIRED = 'Popunite ovo polje.'
BAD_EMAIL = 'Unesite ispravnu email adresu.'


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
        DataRequired(message=REQUIRED),
        Length(min=3, max=64, message='Korisničko ime mora imati od 3 do 64 karaktera.'),
        Regexp('^[A-Za-z0-9_-]+$', message='Korisničko ime može sadržati samo slova, brojeve, _ i -')
    ])
    # Koristimo EmailField umjesto StringField
    email = EmailField('Email', validators=[DataRequired(message=REQUIRED), Email(message=BAD_EMAIL)])
    password = PasswordField('Lozinka', validators=[
        DataRequired(message=REQUIRED),
        Length(min=8, message='Lozinka mora imati najmanje 8 karaktera'),
        validate_password_strength
    ])
    confirm_password = PasswordField('Ponovite lozinku', validators=[
        DataRequired(message=REQUIRED),
        EqualTo('password', message='Lozinke se moraju podudarati.')
    ])
    subscribe = BooleanField('Šaljite mi obavještenja o novim artiklima')
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
    email = EmailField('Email', validators=[DataRequired(message=REQUIRED), Email(message=BAD_EMAIL)])
    password = PasswordField('Lozinka', validators=[DataRequired(message=REQUIRED)])
    remember = BooleanField('Zapamti me na ovom uređaju')
    submit = SubmitField('Prijavi se')

class ProfileForm(FlaskForm):
    first_name = StringField('Ime', validators=[Length(max=64)])
    last_name = StringField('Prezime', validators=[Length(max=64)])
    address = StringField('Adresa', validators=[Length(max=200)])
    city = StringField('Grad', validators=[Length(max=64)])
    postal_code = StringField('Poštanski broj', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^[A-Za-z0-9\s-]+$', message='Poštanski broj može imati samo brojeve i slova, npr. 71000.')
    ])
    country = StringField('Država', validators=[Length(max=64)])
    phone_number = StringField('Broj telefona', validators=[
        Optional(),
        Length(max=20),
        Regexp(r'^\+?[0-9\s()-]+$', message='Unesite broj telefona, npr. 061 123 456.')
    ])
    is_subscribed = BooleanField('Obavještenja o novim artiklima')
    submit = SubmitField('Sačuvaj')