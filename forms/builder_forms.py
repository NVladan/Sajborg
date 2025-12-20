from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, StringField, HiddenField
from wtforms.validators import DataRequired, Email

class PCBuildForm(FlaskForm):
    case = SelectField('Case', coerce=int, validators=[DataRequired()])
    motherboard = SelectField('Motherboard', coerce=int, validators=[DataRequired()])
    cpu = SelectField('CPU', coerce=int, validators=[DataRequired()])
    ram = SelectField('RAM', coerce=int, validators=[DataRequired()])
    storage = SelectField('Storage', coerce=int, validators=[DataRequired()])
    psu = SelectField('Power Supply', coerce=int, validators=[DataRequired()])
    gpu = SelectField('Graphics Card', coerce=int)
    submit = SubmitField('Save Build')

class AddToCartForm(FlaskForm):
    product_id = HiddenField('Product ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired()])
    submit = SubmitField('Add to Cart')

class SubscriptionForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')