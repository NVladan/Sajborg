from flask import Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from models import Product, CartItem, Subscription
from forms.builder_forms import AddToCartForm, SubscriptionForm
from forms.checkout_forms import CheckoutForm
from extensions import limiter

interaction_bp = Blueprint('interaction', __name__, url_prefix='/interaction')


@interaction_bp.route('/subscribe', methods=['POST'])
@limiter.limit("5 per hour", methods=["POST"])
def subscribe():
    form = SubscriptionForm()

    if form.validate_on_submit():
        email = form.email.data

        # Check if already subscribed
        existing = Subscription.query.filter_by(email=email).first()
        if existing:
            flash('Već ste prijavljeni na naš newsletter!', 'info')
        else:
            # Create new subscription
            subscription = Subscription(email=email)
            db.session.add(subscription)

            # If user is logged in, update their subscription status
            if current_user.is_authenticated:
                current_user.is_subscribed = True

            db.session.commit()
            flash('Hvala Vam što ste se prijavljeni na naš newsletter!', 'success')

    # Redirect back to referring page
    next_page = request.referrer or url_for('main.index')
    return redirect(next_page)


@interaction_bp.route('/add-to-cart', methods=['POST'])
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def add_to_cart():
    from flask import current_app
    form = AddToCartForm()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    response = {}
    success = False
    message = ''

    current_app.logger.info(f"Add to cart called for user {current_user.id}")
    current_app.logger.info(f"Request form data: {request.form}")
    current_app.logger.info(f"Form data before validation - product_id: {form.product_id.data}, quantity: {form.quantity.data}")

    if form.validate_on_submit():
        product_id = form.product_id.data
        quantity = form.quantity.data
        extended_warranty = request.form.get('extended_warranty') == 'on'

        current_app.logger.info(f"Adding product {product_id}, quantity {quantity}")

        # Check if product exists and is in stock
        product = Product.query.get_or_404(product_id)
        if product.stock < quantity:
            message = f'Žao nam je, dostupno je samo {product.stock} komada.'
            if is_ajax:
                return jsonify({'success': False, 'message': message})
            flash(message, 'warning')
            return redirect(request.referrer or url_for('product.products'))

        # Check if product is already in cart
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()

        if cart_item:
            # Update quantity
            cart_item.quantity += quantity
            cart_item.extended_warranty = extended_warranty
            message = f'Ažurirana količina za {product.name} u Vašoj korpi.'
        else:
            # Add new item to cart
            cart_item = CartItem(
                user_id=current_user.id,
                product_id=product_id,
                quantity=quantity,
                extended_warranty = extended_warranty
            )
            db.session.add(cart_item)
            message = f'Dodat je {product.name} u Vašu korpu!'

        db.session.commit()
        current_app.logger.info(f"Cart item committed. Cart items now: {len(current_user.cart_items)}")
        # Refresh current_user to update cart_items relationship
        db.session.refresh(current_user)
        current_app.logger.info(f"After refresh, cart items: {len(current_user.cart_items)}")
        success = True

    else:
        current_app.logger.warning(f"Form validation failed: {form.errors}")
        message = 'Neispravno podnošenje forme.'

    if is_ajax:
        return jsonify({'success': success, 'message': message})

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    next_page = request.referrer or url_for('product.products')
    return redirect(next_page)


@interaction_bp.route('/search-suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    # Search for in-stock products
    products = Product.query.filter(Product.stock > 0, Product.name.ilike(f'%{query}%')).order_by(Product.name).limit(
        8).all()
    suggestions = [p.name for p in products]
    return jsonify(suggestions)