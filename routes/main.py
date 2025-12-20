from flask import Blueprint, render_template
from sqlalchemy.orm import joinedload
from models import Product, Category
from forms.builder_forms import SubscriptionForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Get featured products with images eagerly loaded to avoid N+1 queries
    featured_products = Product.query.filter(
        Product.featured == True,
        Product.stock > 0
    ).options(
        joinedload(Product.images)
    ).order_by(Product.created_at.desc()).limit(12).all()

    # Get featured categories - IZMENJENO SA 3 NA 6
    featured_categories = Category.query.filter_by(is_featured=True).limit(6).all()

    # Newsletter subscription form
    form = SubscriptionForm()

    return render_template('index.html',
                           title='Sajborg Shop - Prodaja PC Komponenti i Gaming Opreme',
                           featured_products=featured_products,
                           featured_categories=featured_categories,
                           form=form)

@main_bp.route('/o-nama')
def about():
    return render_template('about.html', title='O nama')

@main_bp.route('/politika-privatnosti')
def privacy_policy():
    return render_template('privacy_policy.html', title='Politika Privatnosti')

@main_bp.route('/uslovi-koriscenja')
def terms_of_use():
    return render_template('terms_of_use.html', title='Uslovi Korišćenja')