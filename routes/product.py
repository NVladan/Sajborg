from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from extensions import db
# ISPRAVKA: Dodajemo 'order_items' u listu za import
from models import Product, Category, ProductAttributeValue, CategoryAttribute, Order, Review, order_items
from forms.builder_forms import AddToCartForm
from forms.review_forms import ReviewForm
import json
from sqlalchemy.orm import aliased, joinedload
from flask_login import current_user, login_required

product_bp = Blueprint('product', __name__)


@product_bp.route('/proizvodi', defaults={'category_slug': None})
@product_bp.route('/proizvodi/<string:category_slug>')
def products(category_slug):
    # Get filter parameters
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'name_asc')
    page = request.args.get('page', 1, type=int)
    attr_filters = request.args.get('attr_filters', '{}')
    try:
        attr_filters = json.loads(attr_filters)
    except json.JSONDecodeError:
        attr_filters = {}

    # Base query
    query = Product.query.filter(Product.stock > 0, Product.is_publicly_visible == True)

    category_id = None
    all_category_ids = []
    # Apply category filter including subcategories
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()
        if selected_category:
            category_id = selected_category.id

            def get_all_child_ids(category):
                """Recursively get all child category IDs."""
                child_ids = [category.id]
                for child in category.subcategories:
                    child_ids.extend(get_all_child_ids(child))
                return child_ids

            all_category_ids = get_all_child_ids(selected_category)
            query = query.filter(Product.category_id.in_(all_category_ids))
        else:
            abort(404)  # If slug is provided but no category found

    # Apply search filter
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    # Apply attribute filters
    if attr_filters:
        for i, (attr_id, value) in enumerate(attr_filters.items()):
            if value and str(attr_id).isdigit():
                pav_alias = aliased(ProductAttributeValue, name=f'pav_{i}')
                query = query.join(pav_alias, Product.id == pav_alias.product_id)
                
                # Convert boolean filter values (1/0) to True/False strings
                if value in ['1', '0']:
                    value = 'True' if value == '1' else 'False'
                
                query = query.filter(
                    pav_alias.attribute_id == int(attr_id),
                    pav_alias.value == value
                )

    # Apply sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name_desc':
        query = query.order_by(Product.name.desc())
    else:  # Default: name_asc
        query = query.order_by(Product.name.asc())

    # Pagination - eager load images and category to avoid N+1 queries
    per_page = 12
    products = query.options(
        joinedload(Product.images),
        joinedload(Product.category)
    ).paginate(page=page, per_page=per_page, error_out=False)

    # Get all categories for filter
    categories = Category.query.all()

    # Get category attributes for the selected category
    category_attributes = []
    attribute_options = {}
    if category_id:
        category = Category.query.get(category_id)
        if category and all_category_ids:
            category_attributes = CategoryAttribute.query.filter_by(category_id=category_id).order_by(
                CategoryAttribute.sort_order).all()

            # Fetch all attribute values in a single query to avoid N+1
            if category_attributes:
                attr_ids = [attr.id for attr in category_attributes]
                all_values = db.session.query(
                    ProductAttributeValue.attribute_id,
                    ProductAttributeValue.value
                ).join(Product).filter(
                    ProductAttributeValue.attribute_id.in_(attr_ids),
                    Product.category_id.in_(all_category_ids),
                    Product.is_publicly_visible == True
                ).distinct().all()

                # Group values by attribute_id
                values_by_attr = {}
                for attr_id, value in all_values:
                    if attr_id not in values_by_attr:
                        values_by_attr[attr_id] = []
                    values_by_attr[attr_id].append(value)

                # Process each attribute
                for attr in category_attributes:
                    values = values_by_attr.get(attr.id, [])

                    # For boolean attributes, convert True/False to Da/Ne for display
                    if attr.type == 'bool':
                        converted_values = []
                        for v in values:
                            if v == 'True':
                                converted_values.append('Da')
                            elif v == 'False':
                                converted_values.append('Ne')
                        attribute_options[attr.id] = sorted(converted_values)
                    else:
                        attribute_options[attr.id] = sorted([v for v in values if v is not None])

    # Add to cart form
    form = AddToCartForm()

    return render_template('shop/products.html',
                           title='Proizvodi',
                           products=products,
                           categories=categories,
                           category_id=category_id,
                           search_query=search_query,
                           sort_by=sort_by,
                           form=form,
                           category_attributes=category_attributes,
                           attr_filters=attr_filters,
                           attribute_options=attribute_options)


@product_bp.route('/product/<string:slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_publicly_visible=True).first_or_404()

    if product.stock <= 0:
        abort(404)

    # Load related products with images to avoid N+1 queries
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.stock > 0,
        Product.is_publicly_visible == True
    ).options(
        joinedload(Product.images)
    ).limit(4).all()

    form = AddToCartForm()
    form.product_id.data = product.id

    # --- NOVO: LOGIKA ZA RECENZIJE ---
    # Load reviews with user data to avoid N+1 queries
    reviews = product.reviews.options(
        joinedload(Review.author)
    ).order_by(Review.created_at.desc()).all()
    review_form = ReviewForm()
    user_can_review = False

    if current_user.is_authenticated:
        # 1. Provjeri da li je korisnik kupio proizvod i da li je narudžba dostavljena
        has_purchased = db.session.query(Order.id).join(order_items).join(Product).filter(
            Order.user_id == current_user.id,
            Order.status == 'dostavljeno',
            Product.id == product.id
        ).first() is not None

        if has_purchased:
            # 2. Provjeri da li je korisnik već ostavio recenziju za ovaj proizvod
            #    (Ovo je jednostavna provjera, složenija logika je u 'add_review' ruti)
            has_reviewed = Review.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
            if not has_reviewed:
                user_can_review = True
    # --- KRAJ NOVE LOGIKE ---

    return render_template('shop/product_detail.html',
                           title=product.name,
                           product=product,
                           related_products=related_products,
                           form=form,
                           reviews=reviews,  # NOVO
                           review_form=review_form,  # NOVO
                           user_can_review=user_can_review)  # NOVO


# --- NOVA RUTA ZA DODAVANJE RECENZIJE ---
@product_bp.route('/product/<int:product_id>/add_review', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()

    if form.validate_on_submit():
        # Pronađi sve dostavljene narudžbe ovog korisnika koje sadrže ovaj proizvod
        eligible_orders = Order.query.join(Order.products).filter(
            Order.user_id == current_user.id,
            Order.status == 'dostavljeno',
            Product.id == product.id
        ).all()

        if not eligible_orders:
            flash('Možete recenzirati samo proizvode koje ste kupili i čija je narudžba dostavljena.', 'warning')
            return redirect(url_for('product.product_detail', slug=product.slug))

        # Provjeri da li je korisnik već ostavio recenziju za ovaj proizvod za bilo koju od podobnih narudžbi
        order_ids = [order.id for order in eligible_orders]
        existing_review = Review.query.filter(
            Review.user_id == current_user.id,
            Review.product_id == product.id,
            Review.order_id.in_(order_ids)
        ).first()

        if existing_review:
            flash('Već ste ostavili recenziju za ovaj proizvod na osnovu vaše kupovine.', 'info')
            return redirect(url_for('product.product_detail', slug=product.slug))

        # Ako nije ostavio recenziju, poveži je sa prvom podobnom narudžbom
        new_review = Review(
            rating=form.rating.data,
            text=form.text.data,
            user_id=current_user.id,
            product_id=product.id,
            order_id=eligible_orders[0].id
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Hvala vam na recenziji!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Greška u polju '{getattr(form, field).label.text}': {error}", 'danger')

    return redirect(url_for('product.product_detail', slug=product.slug))