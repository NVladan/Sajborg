import time
from flask import Blueprint, render_template, make_response, url_for, current_app
from models import Product, Category, Post  # Dodan Post model
from datetime import datetime
from sqlalchemy import func
from extensions import db

seo_bp = Blueprint('seo', __name__)

# Simple in-memory sitemap cache (TTL in seconds)
_sitemap_cache = {'content': None, 'timestamp': 0}
SITEMAP_CACHE_TTL = 3600  # 1 hour


@seo_bp.route('/sitemap.xml')
def sitemap():
    """Generiše sitemap.xml sa dinamičkim prioritetima i datumima izmjene."""
    # Return cached sitemap if still fresh
    now = time.time()
    if _sitemap_cache['content'] and (now - _sitemap_cache['timestamp']) < SITEMAP_CACHE_TTL:
        response = make_response(_sitemap_cache['content'])
        response.headers["Content-Type"] = "application/xml"
        return response

    pages = []

    # Dobavljanje današnjeg datuma jednom za efikasnost
    today = datetime.utcnow().strftime('%Y-%m-%d')

    # Statičke stranice
    # Lista statičkih stranica sa njihovim prioritetima
    static_pages = {
        'main.index': '1.0',
        'main.about': '0.5',
        'main.privacy_policy': '0.3',
        'main.terms_of_use': '0.3',
        'product.products': '0.9',
        'builder.builder': '0.8',
        'blog.all_posts': '0.7'  # Dodana stranica sa svim postovima
    }

    for endpoint, priority in static_pages.items():
        pages.append({
            'loc': url_for(endpoint, _external=True),
            'lastmod': today,
            'priority': priority
        })

    # Proizvodi
    products = Product.query.filter_by(is_publicly_visible=True).all()
    for product in products:
        pages.append({
            'loc': url_for('product.product_detail', slug=product.slug, _external=True),
            'lastmod': product.updated_at.strftime('%Y-%m-%d'),
            'priority': '0.8'
        })

    # Kategorije
    categories = Category.query.filter_by(is_public=True).all()
    for category in categories:
        last_mod_product = db.session.query(func.max(Product.updated_at)).filter(
            Product.category_id == category.id).scalar()
        lastmod = last_mod_product.strftime('%Y-%m-%d') if last_mod_product else today

        pages.append({
            'loc': url_for('product.products', category_slug=category.slug, _external=True),
            'lastmod': lastmod,
            'priority': '0.9'
        })

    # NOVO: Blog postovi
    posts = Post.query.filter_by(is_published=True).all()
    for post in posts:
        pages.append({
            'loc': url_for('blog.view_post', slug=post.slug, _external=True),
            'lastmod': post.updated_at.strftime('%Y-%m-%d'),
            'priority': '0.7'
        })

    sitemap_template = render_template('sitemap.xml', pages=pages)

    # Cache the rendered sitemap
    _sitemap_cache['content'] = sitemap_template
    _sitemap_cache['timestamp'] = time.time()

    response = make_response(sitemap_template)
    response.headers["Content-Type"] = "application/xml"

    return response


@seo_bp.route('/robots.txt')
def robots():
    """Generiše robots.txt. Disallows all crawling on non-production environments."""
    if current_app.debug or current_app.testing:
        lines = [
            "User-agent: *",
            "Disallow: /",
        ]
    else:
        lines = [
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /cart/",
            "Disallow: /checkout/",
            "Disallow: /profile/",
            "",
            f"Sitemap: {url_for('seo.sitemap', _external=True)}"
        ]
    return "\n".join(lines), 200, {"Content-Type": "text/plain"}


@seo_bp.route('/.well-known/security.txt')
def security_txt():
    """Responsible disclosure security.txt (RFC 9116)."""
    lines = [
        f"Contact: mailto:security@sajborg.com",
        f"Preferred-Languages: sr, en",
        f"Canonical: {url_for('seo.security_txt', _external=True)}",
    ]
    return "\n".join(lines), 200, {"Content-Type": "text/plain"}