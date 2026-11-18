"""Smoke testovi: svaka stranica admin panela se otvara u novoj ljusci (bočni meni)."""

import pytest

from extensions import db
from models import CategoryAttribute, AttributeOption, Post, User


@pytest.fixture
def admin_data(app, sample_order, sample_categories):
    category = sample_categories[0]
    attr = CategoryAttribute(category_id=category.id, name='Socket', type='select')
    db.session.add(attr)
    db.session.flush()
    db.session.add(AttributeOption(attribute_id=attr.id, value='AM5'))
    author = User.query.filter_by(role='admin').first()
    db.session.add(Post(title='Test članak', slug='test-clanak', content='<p>x</p>', author_id=author.id))
    db.session.commit()
    product = sample_order.products[0]
    return {'order': sample_order.id, 'category': category.id, 'attribute': attr.id, 'product': product.id,
            'post': Post.query.filter_by(slug='test-clanak').first().id}


def admin_urls(d):
    return [
        '/admin/dashboard',
        '/admin/orders',
        '/admin/orders?status=pending',
        f"/admin/orders/{d['order']}",
        '/admin/products',
        '/admin/products?show_out_of_stock=true',
        '/admin/products/add',
        f"/admin/products/edit/{d['product']}",
        '/admin/categories',
        '/admin/categories/add',
        f"/admin/categories/edit/{d['category']}",
        f"/admin/categories/{d['category']}/attributes",
        f"/admin/attributes/{d['attribute']}/options",
        '/admin/posts',
        '/admin/posts/add',
        f"/admin/posts/edit/{d['post']}",
        '/admin/users',
        '/admin/lager-sync',
    ]


def test_every_admin_page_renders_in_admin_shell(admin_client, admin_data):
    for url in admin_urls(admin_data):
        response = admin_client.get(url)
        assert response.status_code == 200, url
        html = response.get_data(as_text=True)
        assert 'id="adm-sidebar"' in html, url
        assert 'class="footer"' not in html, url  # footer prodavnice se ne prikazuje u adminu


def test_dashboard_shows_order_flow_and_pending_badge(admin_client, admin_data):
    html = admin_client.get('/admin/dashboard').get_data(as_text=True)
    assert 'adm-flow-step is-pending' in html
    assert '/admin/orders?status=pending' in html
    assert 'adm-nav-count is-alert' in html  # brojač porudžbina na čekanju u meniju


def test_shop_pages_keep_their_navigation(client):
    html = client.get('/').get_data(as_text=True)
    assert 'class="footer"' in html
    assert 'adm-sidebar' not in html


def test_categories_are_ordered_by_component_importance(admin_client, app):
    from models import Category
    for name, ct in [('A kuleri', 'CPU Cooler'), ('B procesori', 'CPU'), ('C ostalo', None), ('D grafike', 'GPU')]:
        db.session.add(Category(name=name, slug='ord-' + name[0].lower(), component_type=ct))
    db.session.commit()

    for url in ('/admin/products', '/admin/categories'):
        html = admin_client.get(url).get_data(as_text=True)
        positions = [html.index(n) for n in ('B procesori', 'D grafike', 'A kuleri', 'C ostalo')]
        assert positions == sorted(positions), url


class TestOrderArchive:
    def _order(self, sample_order, status):
        from models import Order
        order = db.session.get(Order, sample_order.id)
        order.status = status
        db.session.commit()
        return order.id

    def test_finished_order_moves_to_archive_and_back(self, admin_client, sample_order):
        from models import Order
        order_id = self._order(sample_order, 'delivered')
        row = f'/admin/orders/{order_id}"'

        assert row in admin_client.get('/admin/orders').get_data(as_text=True)

        admin_client.post(f'/admin/orders/{order_id}/archive', data={'archived': '1'})
        db.session.expire_all()
        assert db.session.get(Order, order_id).archived_at is not None
        assert row not in admin_client.get('/admin/orders').get_data(as_text=True)
        assert row in admin_client.get('/admin/orders?archived=1').get_data(as_text=True)

        admin_client.post(f'/admin/orders/{order_id}/archive', data={'archived': '0'})
        db.session.expire_all()
        assert db.session.get(Order, order_id).archived_at is None
        assert row in admin_client.get('/admin/orders').get_data(as_text=True)

    def test_unfinished_order_cannot_be_archived(self, admin_client, sample_order):
        from models import Order
        order_id = self._order(sample_order, 'pending')
        admin_client.post(f'/admin/orders/{order_id}/archive', data={'archived': '1'})
        db.session.expire_all()
        assert db.session.get(Order, order_id).archived_at is None

    def test_archive_redirect_stays_inside_admin(self, admin_client, sample_order):
        order_id = self._order(sample_order, 'cancelled')
        response = admin_client.post(f'/admin/orders/{order_id}/archive',
                                     data={'archived': '1', 'next': 'https://evil.example/'})
        assert response.headers['Location'].endswith(f'/admin/orders/{order_id}')
