from flask import Blueprint, redirect, url_for, flash, request
from flask_login import current_user
from functools import wraps
from extensions import limiter

# Define the admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Apply rate limits to all admin POST endpoints (prevents brute-force/abuse)
limiter.limit("60 per minute", methods=["POST"])(admin_bp)

# Decorator to check for admin privileges
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Neprijavljen korisnik ide na prijavu i poslije nje se vraća na traženu admin stranicu
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.full_path.rstrip('?')))
        if current_user.role != 'admin':
            flash('Nemate dozvolu za pristup ovoj stranici.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Redoslijed kategorija u adminu: po važnosti komponente za računar (prema tipu u PC konfiguratoru)
COMPONENT_IMPORTANCE = ('CPU', 'Motherboard', 'GPU', 'RAM', 'Storage', 'Power Supply', 'Case',
                        'CPU Cooler', 'Case Fans', 'Monitor', 'Keyboard', 'Mouse')


def category_rank_expr():
    """SQL izraz za ORDER BY: važnije komponente prvo, kategorije bez tipa na kraju."""
    from sqlalchemy import case
    from models import Category
    return case({ct: i for i, ct in enumerate(COMPONENT_IMPORTANCE)},
                value=Category.component_type, else_=len(COMPONENT_IMPORTANCE))


def safe_products_next(value):
    """Povratna adresa na listu proizvoda (tab, pretraga, strana) — samo lokalni /admin/products URL."""
    if value and value.startswith('/admin/products') and not value.startswith('//'):
        return value
    return None

# Import routes to register them with the blueprint
from . import dashboard, product_routes, category_routes, order_routes, user_routes, product_image_routes, blog_routes, lager_sync_routes