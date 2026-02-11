from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SubmitField, SelectField, FileField, \
    BooleanField
# IZMJENA: Uvozimo InputRequired umjesto DataRequired za polje zaliha
from wtforms.validators import DataRequired, NumberRange, InputRequired, Length


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    # IZMJENA: Koristimo InputRequired() umjesto DataRequired() da bi vrijednost 0 bila važeća
    stock = IntegerField('Stock', validators=[InputRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    # NOVO: Polje za stanje proizvoda
    condition = SelectField('Stanje', choices=[('Novo', 'Novo'), ('Polovno', 'Polovno')], validators=[DataRequired()])
    # NOVO: Polje za dostupnost proizvoda
    availability = SelectField('Dostupnost', choices=[('Dostupno odmah', 'Dostupno odmah'), ('Dostupno za 7 dana', 'Dostupno za 7 dana'), ('Dostupno za 14 dana', 'Dostupno za 14 dana')], validators=[DataRequired()])
    specs = TextAreaField('Specifications')
    featured = BooleanField('Featured Product')
    images = FileField('Product Images', render_kw={'multiple': True})
    submit = SubmitField('Add Product')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    slug = StringField('Slug')
    description = TextAreaField('Description')
    parent_id = SelectField('Parent Category', coerce=int)
    component_type = SelectField('PC Builder Component Type', choices=[('', 'N/A')])
    image = FileField('Category Image')
    is_featured = BooleanField('Featured Category')
    submit = SubmitField('Create Category')


class ImportForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Import Products')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired(), Length(max=100000, message='Sadržaj članka je predugačak (max 100.000 karaktera).')])
    featured_image = FileField('Featured Image')
    is_published = BooleanField('Published')
    submit = SubmitField('Submit')