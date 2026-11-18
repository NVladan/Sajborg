"""Prijava, registracija i profil kupca."""

from extensions import db
from models import Order, User, order_items


def test_login_page_is_in_serbian_and_keeps_next(client):
    html = client.get('/login?next=/proizvodi').get_data(as_text=True)
    assert 'Remember Me' not in html and 'Password' not in html
    assert 'Zapamti me' in html
    assert 'action="/login?next=/proizvodi"' in html          # next ostaje i pri slanju forme


def test_login_redirects_back_to_next(client, sample_user):
    res = client.post('/login?next=/proizvodi', data={'email': 'test@example.com', 'password': 'Password123'})
    assert res.headers['Location'].endswith('/proizvodi')


def test_login_ignores_foreign_next(client, sample_user):
    for bad in ('https://evil.example/', '//evil.example/', '/\\evil.example'):
        client.get('/logout')
        res = client.post('/login?next=' + bad, data={'email': 'test@example.com', 'password': 'Password123'})
        assert 'evil' not in res.headers['Location'], bad


def test_wrong_password_shows_message(client, sample_user):
    res = client.post('/login', data={'email': 'test@example.com', 'password': 'pogresno'}, follow_redirects=True)
    assert 'Email ili lozinka nisu tačni.' in res.get_data(as_text=True)


def test_register_logs_in_and_returns_to_next(client, app):
    res = client.post('/register?next=/cart', data={
        'username': 'novi_kupac', 'email': 'novi@example.com', 'password': 'Lozinka123',
        'confirm_password': 'Lozinka123',
    })
    assert res.headers['Location'].endswith('/cart')
    assert client.get('/cart').status_code == 200                # prijavljen odmah nakon registracije


def test_register_errors_in_serbian(client):
    html = client.post('/register', data={'email': 'nije-email', 'password': 'kratka'}).get_data(as_text=True)
    assert 'This field is required' not in html
    assert 'Popunite ovo polje.' in html
    assert 'Unesite ispravnu email adresu.' in html


def test_profile_shows_real_order_quantities_and_prices(auth_client, sample_product):
    user = User.query.filter_by(email='test@example.com').first()
    order = Order(user_id=user.id, total_amount=1210.0, status='shipped', shipping_first_name='Test',
                  shipping_address='Ulica 1', shipping_city='Sarajevo', shipping_postal_code='71000')
    db.session.add(order)
    db.session.flush()
    # Cijena u narudžbi je bila 600 KM, a sada je 299,99; količina je 2
    db.session.execute(order_items.insert().values(order_id=order.id, product_id=sample_product.id,
                                                   quantity=2, price=600.0))
    db.session.commit()

    html = auth_client.get('/profile').get_data(as_text=True)
    assert f'Narudžba #{order.id}' in html
    assert '2 × 600,00' in html
    assert '1.200,00' in html
    assert 'Poslata' in html and 'Shipped' not in html


def test_profile_saves_with_empty_postal_code(auth_client):
    res = auth_client.post('/profile', data={'first_name': 'Ana', 'city': 'Mostar', 'postal_code': '', 'phone_number': ''})
    assert res.status_code == 302
    user = User.query.filter_by(email='test@example.com').first()
    db.session.refresh(user)
    assert (user.first_name, user.city) == ('Ana', 'Mostar')


def test_login_required_message_is_serbian(client):
    res = client.get('/profile', follow_redirects=True)
    html = res.get_data(as_text=True)
    assert 'Please log in' not in html
    assert 'Prijavite se da biste nastavili.' in html
