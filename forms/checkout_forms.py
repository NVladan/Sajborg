from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class CheckoutForm(FlaskForm):
    first_name = StringField('Ime', validators=[DataRequired()])
    last_name = StringField('Prezime', validators=[DataRequired()])
    address = StringField('Adresa', validators=[DataRequired()])
    city = StringField('Grad', validators=[DataRequired()])
    postal_code = StringField('Poštanski broj', validators=[DataRequired()])
    country = StringField('Država', validators=[DataRequired()])
    phone_number = StringField('Broj telefona', validators=[DataRequired()])
    payment_method = SelectField('Način plaćanja', choices=[('cash_on_delivery', 'Plaćanje pouzećem')], validators=[DataRequired()])
    submit = SubmitField('Naručite')