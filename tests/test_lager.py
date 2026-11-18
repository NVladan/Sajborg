"""Lager stranica (/lager/)."""

import pytest

from extensions import db
from models import LagerCategory, LagerProduct, User


@pytest.fixture
def lager_items(app):
    main = LagerCategory(name='CPU', slug='v2-cpu')
    db.session.add(main)
    db.session.flush()
    sub = LagerCategory(name='AMD', slug='v2-cpu-amd', parent_id=main.id)
    db.session.add(sub)
    db.session.flush()
    in_stock = LagerProduct(name='AMD Ryzen 5 5600', stock=2, purchase_price=200, category_id=sub.id,
                            reservation_note='Marko')
    sold_out = LagerProduct(name='AMD Ryzen 5 3600', stock=0, purchase_price=139, category_id=sub.id)
    db.session.add_all([in_stock, sold_out])
    db.session.commit()
    return {'in_stock': in_stock.id, 'sold_out': sold_out.id}


def login_as(client, role):
    user = User(username=f'lager_{role}', email=f'lager_{role}@example.com', role=role)
    user.set_password('Lager123!')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': user.email, 'password': 'Lager123!'})
    return client


def test_admin_sees_all_items_with_value(admin_client, lager_items):
    html = admin_client.get('/lager/').get_data(as_text=True)
    assert 'AMD Ryzen 5 5600' in html
    assert 'AMD Ryzen 5 3600' in html          # bez stanja, skriva se u pregledaču prekidačem
    assert '400,00' in html                    # 2 x 200 KM nabavna vrijednost
    assert 'lg-step-btn' in html               # admin mijenja količinu
    assert 'Marko' in html                     # rezervacija


def test_distributer_never_gets_sold_out_items_or_stock_buttons(client, lager_items):
    html = login_as(client, 'distributer').get('/lager/').get_data(as_text=True)
    assert 'AMD Ryzen 5 5600' in html
    assert 'AMD Ryzen 5 3600' not in html
    assert 'lg-step-btn' not in html
    assert 'name="product_name"' not in html   # distributer mijenja samo napomene


def test_customer_has_no_access(auth_client, lager_items):
    assert auth_client.get('/lager/', follow_redirects=False).status_code == 302


def test_save_returns_to_same_category(admin_client, lager_items):
    item_id = lager_items['in_stock']
    response = admin_client.post(f'/lager/update_details/{item_id}', data={
        'product_name': 'AMD Ryzen 5 5600 BOX', 'stock': '3', 'purchase_price': '210,50',
        'reservation_note': '', 'internal_note': 'test', 'active_tab_slug': 'CPU',
    })
    assert response.headers['Location'].endswith('/lager/?active_tab=CPU')
    db.session.expire_all()
    item = db.session.get(LagerProduct, item_id)
    assert (item.name, item.stock, item.purchase_price) == ('AMD Ryzen 5 5600 BOX', 3, 210.5)


def test_old_v2_link_redirects_to_lager(admin_client, lager_items):
    response = admin_client.get('/lager/v2?active_tab=CPU')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/lager/?active_tab=CPU')
