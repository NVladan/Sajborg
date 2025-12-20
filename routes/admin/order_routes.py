from flask import render_template, redirect, url_for, flash, request
from sqlalchemy.orm import joinedload
from extensions import db
from models import Product, Category, Order, User, ProductImage, order_items as order_items_table
from . import admin_bp, admin_required


@admin_bp.route('/orders')
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'created_desc')

    # Eager load user data to avoid N+1 queries
    query = Order.query.join(User).options(joinedload(Order.user))

    if status:
        query = query.filter(Order.status == status)

    if search_query:
        query = query.filter(
            (Order.id.like(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        )

    if sort_by == 'id_asc':
        query = query.order_by(Order.id.asc())
    elif sort_by == 'id_desc':
        query = query.order_by(Order.id.desc())
    elif sort_by == 'total_asc':
        query = query.order_by(Order.total_amount.asc())
    elif sort_by == 'total_desc':
        query = query.order_by(Order.total_amount.desc())
    elif sort_by == 'created_asc':
        query = query.order_by(Order.created_at.asc())
    else:
        query = query.order_by(Order.created_at.desc())

    orders_pagination = query.paginate(page=page, per_page=10, error_out=False)

    return render_template('admin/orders.html',
                           title='Upravljanje Porudžbinama',
                           orders=orders_pagination,
                           status=status,
                           search_query=search_query,
                           sort_by=sort_by)


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    # Fetch all order items in a single query to avoid N+1
    stmt = db.select(
        order_items_table.c.product_id,
        order_items_table.c.quantity,
        order_items_table.c.price,
        order_items_table.c.extended_warranty
    ).where(order_items_table.c.order_id == order.id)

    order_items_data = db.session.execute(stmt).all()

    # Create a mapping of product_id to quantity/price/extended_warranty
    items_map = {item.product_id: (item.quantity, item.price, item.extended_warranty) for item in order_items_data}

    # Build the order items list
    order_items_with_subtotals = []
    for product in order.products:
        if product.id in items_map:
            quantity, price, extended_warranty = items_map[product.id]
            subtotal = quantity * price
            order_items_with_subtotals.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'extended_warranty': extended_warranty,
                'subtotal': subtotal
            })

    return render_template('admin/order_detail.html',
                           title=f'Detalji Porudžbine #{order.id}',
                           order=order,
                           order_items=order_items_with_subtotals)


@admin_bp.route('/orders/update-status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    # Dozvoljeni statusi: Na čekanju, U pripremi, Poslato, Dostavljeno, Otkazano
    if status in ['pending', 'preparing', 'shipped', 'delivered', 'cancelled']:
        order.status = status
        db.session.commit()
        flash('Status porudžbine je uspešno ažuriran.', 'success')
    else:
        flash('Došlo je do greške prilikom ažuriranja statusa.', 'danger')
    return redirect(url_for('admin.order_detail', order_id=order.id))