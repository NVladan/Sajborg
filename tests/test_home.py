"""Početna strana."""

from extensions import db
from models import Category, Product


def test_home_shows_stock_categories_and_builder(client, app):
    cat = Category(name='Procesori', slug='home-cpu', component_type='CPU', is_featured=True,
                   image_path='img/category-default.png')
    db.session.add(cat)
    db.session.flush()
    db.session.add_all([
        Product(name='Ryzen 5 7600', slug='home-7600', price=1234.5, stock=2, category_id=cat.id,
                component_type='CPU', is_publicly_visible=True, featured=True),
        Product(name='Rasprodat CPU', slug='home-sold', price=99, stock=0, category_id=cat.id,
                component_type='CPU', is_publicly_visible=False),
    ])
    db.session.commit()

    html = client.get('/').get_data(as_text=True)
    assert 'Ryzen 5 7600' in html
    assert '1.234,50' in html                 # cijena u BiH formatu
    assert 'Rasprodat CPU' not in html
    assert '1 na stanju' in html              # broj artikala u kategoriji
    assert 'Otvori konfigurator' in html
    assert 'od 1.235' in html                 # najniža cijena procesora u najavi konfiguratora


def test_products_can_be_sorted_newest_first(client):
    assert client.get('/proizvodi?sort=newest').status_code == 200
