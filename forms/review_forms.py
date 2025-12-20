from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class ReviewForm(FlaskForm):
    """
    Forma za kreiranje i izmjenu recenzija proizvoda.
    """
    rating = IntegerField(
        'Ocjena (1-5)',
        validators=[
            DataRequired(message="Molimo unesite ocjenu."),
            NumberRange(min=1, max=5, message="Ocjena mora biti između 1 i 5.")
        ],
        render_kw={"class": "form-control", "min": "1", "max": "5", "step": "1"}
    )
    text = TextAreaField(
        'Vaša recenzija',
        validators=[DataRequired(message="Molimo napišite recenziju.")],
        render_kw={"class": "form-control", "rows": 5, "placeholder": "Napišite svoje mišljenje o proizvodu..."}
    )
    submit = SubmitField(
        'Pošalji recenziju',
        render_kw={"class": "btn btn-primary mt-3"}
    )