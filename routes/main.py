from flask import Blueprint, render_template, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy import text, func
from extensions import db
from models import Product, Category, Post
from pc_build_check import SLOTS
from routes.admin import category_rank_expr

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    in_stock = (Product.stock > 0, Product.is_publicly_visible.is_(True))

    featured_products = (Product.query.filter(Product.featured.is_(True), *in_stock)
                         .options(joinedload(Product.images), joinedload(Product.category))
                         .order_by(Product.created_at.desc()).limit(8).all())
    featured_ids = {p.id for p in featured_products}
    new_products = [p for p in (Product.query.filter(*in_stock)
                                .options(joinedload(Product.images), joinedload(Product.category))
                                .order_by(Product.created_at.desc()).limit(16).all())
                    if p.id not in featured_ids][:4]

    # Istaknute kategorije, poredane po važnosti komponente, sa brojem artikala na stanju
    counts = dict(db.session.query(Product.category_id, func.count(Product.id))
                  .filter(*in_stock).group_by(Product.category_id).all())
    featured_categories = (Category.query.filter_by(is_featured=True)
                           .order_by(category_rank_expr(), Category.name).limit(8).all())
    for cat in featured_categories:
        cat.in_stock = counts.get(cat.id, 0) + sum(counts.get(sub.id, 0) for sub in cat.subcategories)

    # Najava konfiguratora: slotovi sa slikom kategorije i najnižom cijenom na stanju
    min_prices = dict(db.session.query(Product.component_type, func.min(Product.price))
                      .filter(Product.component_type.isnot(None), *in_stock)
                      .group_by(Product.component_type).all())
    images = {}
    for cat in Category.query.filter(Category.component_type.isnot(None)).order_by(Category.parent_id.isnot(None)).all():
        if cat.image_path and cat.component_type not in images:
            images[cat.component_type] = cat.image_path
    builder_slots = [{'label': label, 'image': images.get(key), 'from_price': min_prices.get(key)}
                     for key, label, _, _ in SLOTS if key in min_prices][:5]

    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(3).all()

    return render_template('index.html',
                           title='Sajborg Shop - Prodaja PC Komponenti i Gaming Opreme',
                           featured_products=featured_products,
                           new_products=new_products,
                           featured_categories=featured_categories,
                           builder_slots=builder_slots,
                           in_stock_total=Product.query.filter(*in_stock).count(),
                           posts=posts)

@main_bp.route('/o-nama')
def about():
    return render_template('about.html', title='O nama')

@main_bp.route('/politika-privatnosti')
def privacy_policy():
    return render_template('privacy_policy.html', title='Politika Privatnosti')

@main_bp.route('/uslovi-koriscenja')
def terms_of_use():
    return render_template('terms_of_use.html', title='Uslovi Korišćenja')


@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'ok'}), 200
    except Exception:
        return jsonify({'status': 'unhealthy', 'database': 'error'}), 503