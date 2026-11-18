"""Put do kupovine: lista proizvoda, proizvod, korpa, checkout, potvrda."""

import json

from extensions import db
from models import CartItem, CategoryAttribute, Order, Product, ProductAttributeValue, Review, User, order_items


def add_attr(product, name, value, attr_type='string'):
    attr = CategoryAttribute.query.filter_by(category_id=product.category_id, name=name).first()
    if not attr:
        attr = CategoryAttribute(category_id=product.category_id, name=name, type=attr_type)
        db.session.add(attr)
        db.session.flush()
    db.session.add(ProductAttributeValue(product_id=product.id, attribute_id=attr.id, value=value))
    db.session.commit()
    return attr


def test_product_list_shows_cards_filters_and_bih_prices(client, sample_product):
    attr = add_attr(sample_product, 'socket', 'AM4')
    html = client.get('/proizvodi/procesori').get_data(as_text=True)
    assert 'AMD Ryzen 5 5600X' in html
    assert '299,99' in html                     # cijena u formatu 299,99 KM
    assert 'Na izmaku' not in html
    assert 'AM4' in html                        # filter kao chip

    filtered = client.get('/proizvodi/procesori?attr_filters=' + json.dumps({str(attr.id): 'AM5'})).get_data(as_text=True)
    assert 'AMD Ryzen 5 5600X' not in filtered
    assert 'Očisti filtere' in filtered


def test_product_detail(client, sample_product):
    add_attr(sample_product, 'socket', 'AM4')
    html = client.get(f'/product/{sample_product.slug}').get_data(as_text=True)
    assert 'Specifikacije' in html and 'AM4' in html
    assert 'Prijavite se da naručite' in html   # gost
    assert 'pravatar' not in html               # bez vanjskih avatara


def test_logged_in_buy_flow(auth_client, sample_product, sample_user):
    html = auth_client.get(f'/product/{sample_product.slug}').get_data(as_text=True)
    assert 'Dodaj u korpu' in html and 'Produžena garancija' in html

    res = auth_client.post('/interaction/add-to-cart', data={'product_id': sample_product.id, 'quantity': 2},
                           headers={'X-Requested-With': 'XMLHttpRequest'})
    assert res.get_json()['success']

    cart = auth_client.get('/cart').get_data(as_text=True)
    assert 'AMD Ryzen 5 5600X' in cart and '599,98' in cart

    checkout = auth_client.get('/checkout').get_data(as_text=True)
    assert 'Podaci za dostavu' in checkout and 'Potvrdi narudžbu' in checkout
    assert 'autocomplete="tel"' in checkout
    assert '="None"' not in checkout

    res = auth_client.post('/checkout', data={
        'first_name': 'Test', 'last_name': 'Kupac', 'address': 'Ulica 1', 'city': 'Sarajevo',
        'postal_code': '71000', 'country': 'BiH', 'phone_number': '061111111', 'payment_method': 'cash_on_delivery',
    })
    assert '/checkout/success' in res.headers['Location']
    done = auth_client.get(res.headers['Location']).get_data(as_text=True)
    assert 'je primljena' in done and 'Email sa potvrdom' not in done


def test_empty_cart(auth_client):
    html = auth_client.get('/cart').get_data(as_text=True)
    assert 'Korpa je prazna' in html


def test_review_allowed_after_delivered_order(auth_client, sample_product, sample_user):
    user = User.query.filter_by(email='test@example.com').first()
    order = Order(user_id=user.id, total_amount=299.99, status='delivered')
    db.session.add(order)
    db.session.flush()
    db.session.execute(order_items.insert().values(order_id=order.id, product_id=sample_product.id, quantity=1, price=299.99))
    db.session.commit()

    html = auth_client.get(f'/product/{sample_product.slug}').get_data(as_text=True)
    assert 'Objavi recenziju' in html          # ranije je tražilo status 'dostavljeno' koji admin ne postavlja

    auth_client.post(f'/product/{sample_product.id}/add_review', data={'rating': 4, 'text': 'Odličan'})
    assert Review.query.filter_by(product_id=sample_product.id).count() == 1
