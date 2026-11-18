from datetime import datetime, timedelta

from flask import render_template
from sqlalchemy import func

from extensions import db
from models import Product, Order, User, Post
from . import admin_bp, admin_required
from .lager_sync_routes import build_sync_overview

# Redoslijed kojim porudžbina prolazi kroz obradu (prikazuje se kao tok na dashboardu)
ORDER_FLOW = (
    ('pending', 'Na čekanju'),
    ('preparing', 'U pripremi'),
    ('shipped', 'Poslato'),
    ('delivered', 'Dostavljeno'),
)
DELIVERED_ALIASES = ('delivered', 'dostavljeno')
REVENUE_DAYS = 30


@admin_bp.app_context_processor
def admin_nav_counts():
    """Brojač porudžbina na čekanju za bočni meni admin panela."""
    from flask import request
    if not request.blueprint == 'admin':
        return {}
    return {'nav_pending_orders': Order.query.filter_by(status='pending').count()}


def _order_status_counts():
    rows = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    counts = {status: n for status, n in rows}
    counts['delivered'] = sum(counts.pop(alias, 0) for alias in DELIVERED_ALIASES)
    return counts


def _daily_revenue(days=REVENUE_DAYS):
    """Promet po danu (bez otkazanih) za zadnjih `days` dana, najstariji prvi."""
    today = datetime.utcnow().date()
    start = today - timedelta(days=days - 1)
    rows = (db.session.query(func.date(Order.created_at), func.sum(Order.total_amount), func.count(Order.id))
            .filter(Order.created_at >= datetime.combine(start, datetime.min.time()),
                    Order.status != 'cancelled')
            .group_by(func.date(Order.created_at))
            .all())
    by_day = {str(day): (float(total or 0), n) for day, total, n in rows}
    series = []
    for i in range(days):
        day = start + timedelta(days=i)
        total, n = by_day.get(day.isoformat(), (0.0, 0))
        series.append({'date': day, 'total': total, 'orders': n})
    return series


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    status_counts = _order_status_counts()
    flow = [{'key': key, 'label': label, 'count': status_counts.get(key, 0)} for key, label in ORDER_FLOW]

    revenue = _daily_revenue()
    revenue_total = sum(d['total'] for d in revenue)
    revenue_orders = sum(d['orders'] for d in revenue)
    revenue_max = max((d['total'] for d in revenue), default=0)

    sync = build_sync_overview(with_suggestions=False)
    no_image_count = (Product.query
                      .filter(Product.is_publicly_visible.is_(True), ~Product.images.any())
                      .count())

    attention = [
        {'count': status_counts.get('pending', 0), 'label': 'porudžbina čeka obradu',
         'endpoint': 'admin.orders', 'args': {'status': 'pending'}, 'icon': 'fa-inbox'},
        {'count': len(sync['mismatched']), 'label': 'proizvoda ima drugačije stanje ili cijenu nego lager',
         'endpoint': 'admin.lager_sync', 'args': {'_anchor': 'uskladi'}, 'icon': 'fa-rotate'},
        {'count': sum(len(rows) for rows in sync['unpublished'].values()),
         'label': 'artikala sa lagera još nije na sajtu',
         'endpoint': 'admin.lager_sync', 'args': {'_anchor': 'objavi'}, 'icon': 'fa-upload'},
        {'count': len(sync['unlinked_rows']), 'label': 'proizvoda na sajtu nije povezano sa lagerom',
         'endpoint': 'admin.lager_sync', 'args': {'_anchor': 'povezi'}, 'icon': 'fa-link-slash'},
        {'count': no_image_count, 'label': 'vidljivih proizvoda nema sliku',
         'endpoint': 'admin.products', 'args': {}, 'icon': 'fa-image'},
    ]

    recent_orders = (Order.query.filter(Order.archived_at.is_(None))
                     .order_by(Order.created_at.desc()).limit(6).all())

    return render_template('admin/dashboard.html',
                           title='Pregled',
                           flow=flow,
                           cancelled_count=Order.query.filter(Order.status == 'cancelled',
                                                              Order.archived_at.is_(None)).count(),
                           revenue=revenue,
                           revenue_total=revenue_total,
                           revenue_orders=revenue_orders,
                           revenue_max=revenue_max,
                           revenue_days=REVENUE_DAYS,
                           attention=attention,
                           recent_orders=recent_orders,
                           archived_orders=Order.query.filter(Order.archived_at.isnot(None)).count(),
                           total_products=Product.query.filter_by(is_publicly_visible=True).count(),
                           total_users=User.query.count(),
                           total_posts=Post.query.count())
