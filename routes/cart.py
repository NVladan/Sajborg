import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from sqlalchemy import text
from extensions import db, limiter
from models import CartItem, Product, Order, order_items
from forms.checkout_forms import CheckoutForm
from utils import calculate_order_total

cart_bp = Blueprint('cart', __name__)


@cart_bp.route('/cart')
@login_required
def view_cart():
    # Eagerly load products to avoid N+1 queries
    cart_items = CartItem.query.filter_by(user_id=current_user.id).options(
        joinedload(CartItem.product)
    ).all()
    subtotal = calculate_order_total(cart_items)
    shipping_cost = current_app.config.get('SHIPPING_COST', 10.0)
    total = subtotal + shipping_cost

    return render_template('shop/cart.html',
                           title='Korpa',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping_cost=shipping_cost,
                           total=total)


@cart_bp.route('/cart/update', methods=['POST'])
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def update_cart():
    try:
        cart_data = request.json

        for item_id, data in cart_data.items():
            item_id = int(item_id)
            quantity = int(data.get('quantity', 1))
            extended_warranty = bool(data.get('extended_warranty', False))

            cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()

            if cart_item:
                if quantity <= 0:
                    db.session.delete(cart_item)
                else:
                    if quantity > cart_item.product.stock:
                        return jsonify({
                            'success': False,
                            'message': f'Samo {cart_item.product.stock} komada proizvoda {cart_item.product.name} je dostupno.'
                        })
                    cart_item.quantity = quantity
                    # Ažuriramo i status garancije
                    if cart_item.product.condition == 'Novo':
                        cart_item.extended_warranty = extended_warranty

        db.session.commit()

        # Eagerly load products to avoid N+1 queries
        cart_items = CartItem.query.filter_by(user_id=current_user.id).options(
            joinedload(CartItem.product)
        ).all()
        subtotal = calculate_order_total(cart_items)
        shipping_cost = current_app.config.get('SHIPPING_COST', 10.0)
        total = subtotal + shipping_cost

        return jsonify({
            'success': True,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total
        })

    except Exception as e:
        current_app.logger.error(f"Error updating cart: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        })


@cart_bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
@limiter.limit("30 per minute", methods=["POST"])
def remove_from_cart(item_id):
    cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()

    product_name = cart_item.product.name
    db.session.delete(cart_item)
    db.session.commit()

    flash(f'Uklonjen je {product_name} iz Vaše korpe.', 'success')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def checkout():
    # Get cart items with eager loading to avoid N+1 queries
    cart_items = CartItem.query.filter_by(user_id=current_user.id).options(
        joinedload(CartItem.product)
    ).all()

    # If cart is empty, redirect to cart page
    if not cart_items:
        flash('Vaša korpa je prazna.', 'info')
        return redirect(url_for('cart.view_cart'))

    # Calculate total
    subtotal = calculate_order_total(cart_items)
    shipping_cost = current_app.config.get('SHIPPING_COST', 10.0)
    total = subtotal + shipping_cost

    # Create checkout form
    form = CheckoutForm()

    # Pre-populate form with user data
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.postal_code.data = current_user.postal_code
        form.country.data = current_user.country
        form.phone_number.data = current_user.phone_number

    if form.validate_on_submit():
        try:
            # Re-fetch cart items inside transaction for consistency
            cart_items = CartItem.query.filter_by(user_id=current_user.id).options(
                joinedload(CartItem.product)
            ).all()

            if not cart_items:
                flash('Vaša korpa je prazna.', 'info')
                return redirect(url_for('cart.view_cart'))

            # Lock products to prevent race conditions on stock
            product_ids = [item.product_id for item in cart_items]
            locked_products = Product.query.filter(
                Product.id.in_(product_ids)
            ).with_for_update().all()
            product_map = {p.id: p for p in locked_products}

            # Validate stock availability with locked rows
            for item in cart_items:
                product = product_map.get(item.product_id)
                if not product:
                    db.session.rollback()
                    flash(f'Proizvod iz korpe više nije dostupan.', 'danger')
                    return redirect(url_for('cart.view_cart'))
                if product.stock < item.quantity:
                    db.session.rollback()
                    flash(f'Nedovoljna količina za {product.name}. Dostupno: {product.stock}.', 'danger')
                    return redirect(url_for('cart.view_cart'))

            # Recalculate total with locked prices
            subtotal = calculate_order_total(cart_items)
            shipping_cost = current_app.config.get('SHIPPING_COST', 10.0)
            total = subtotal + shipping_cost

            # Create order
            order = Order(
                user_id=current_user.id,
                total_amount=total,
                payment_method='cash_on_delivery',
                status='pending',
                shipping_first_name=form.first_name.data,
                shipping_last_name=form.last_name.data,
                shipping_address=form.address.data,
                shipping_city=form.city.data,
                shipping_postal_code=form.postal_code.data,
                shipping_country=form.country.data,
                shipping_phone_number=form.phone_number.data
            )

            db.session.add(order)
            db.session.flush()  # Get order ID

            # Add products to order and decrement stock atomically
            for item in cart_items:
                product = product_map[item.product_id]

                stmt = order_items.insert().values(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=product.price,
                    extended_warranty=item.extended_warranty
                )
                db.session.execute(stmt)

                # Decrement stock (row is locked via with_for_update)
                product.stock -= item.quantity

            # Clear cart
            CartItem.query.filter_by(user_id=current_user.id).delete()

            # Commit entire transaction atomically
            db.session.commit()
            flash('Vaša porudžbina je uspešno kreirana! Platićete prilikom isporuke.', 'success')
            return redirect(url_for('cart.checkout_success', order_id=order.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Checkout error: {e}")
            flash('Došlo je do greške pri kreiranju porudžbine. Pokušajte ponovo.', 'danger')
            return redirect(url_for('cart.view_cart'))

    return render_template('shop/checkout.html',
                           title='Plaćanje',
                           form=form,
                           cart_items=cart_items,
                           subtotal=subtotal,
                           shipping_cost=shipping_cost,
                           total=total)


@cart_bp.route('/checkout/success')
@login_required
def checkout_success():
    order_id = request.args.get('order_id', type=int)

    # Verify that the order belongs to the current user
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

    return render_template('shop/checkout_success.html',
                           title='Porudžbina uspešna',
                           order=order)


@cart_bp.route('/checkout/cancel')
@login_required
def checkout_cancel():
    order_id = request.args.get('order_id', type=int)

    # Verify that the order belongs to the current user
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()

    # Update order status
    order.status = 'cancelled'
    db.session.commit()

    return render_template('shop/checkout_cancel.html',
                           title='Porudžbina otkazana',
                           order=order)