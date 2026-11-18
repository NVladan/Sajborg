from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

class CheckoutForm(FlaskForm):
    first_name = StringField('Ime', validators=[DataRequired(message='Popunite ovo polje.')])
    last_name = StringField('Prezime', validators=[DataRequired(message='Popunite ovo polje.')])
    address = StringField('Adresa', validators=[DataRequired(message='Popunite ovo polje.')])
    city = StringField('Grad', validators=[DataRequired(message='Popunite ovo polje.')])
    postal_code = StringField('Poštanski broj', validators=[DataRequired(message='Popunite ovo polje.')])
    country = StringField('Država', validators=[DataRequired(message='Popunite ovo polje.')])
    phone_number = StringField('Broj telefona', validators=[DataRequired(message='Popunite ovo polje.')])
    payment_method = SelectField('Način plaćanja', choices=[('cash_on_delivery', 'Plaćanje pouzećem')], validators=[DataRequired(message='Popunite ovo polje.')])
    submit = SubmitField('Naručite')