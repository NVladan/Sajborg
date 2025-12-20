from flask import render_template
from models import Product, Order, User
from . import admin_bp, admin_required

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Get stats for dashboard
    # IZMJENA OVDJE: Brojimo samo proizvode koji su javno vidljivi
    total_products = Product.query.filter_by(is_publicly_visible=True).count()
    total_orders = Order.query.count()
    total_users = User.query.count()

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           title='Admin Panel',
                           total_products=total_products,
                           total_orders=total_orders,
                           total_users=total_users,
                           recent_orders=recent_orders)