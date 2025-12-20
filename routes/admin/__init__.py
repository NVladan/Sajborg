from flask import Blueprint, redirect, url_for, flash
from flask_login import current_user
from functools import wraps

# Define the admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator to check for admin privileges
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # IZMENJENA LINIJA: Proveravamo da li je uloga 'admin' umesto starog is_admin polja
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Nemate dozvolu za pristup ovoj stranici.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# Import routes to register them with the blueprint
from . import dashboard, product_routes, category_routes, order_routes, user_routes, product_image_routes, product_import_routes, blog_routes