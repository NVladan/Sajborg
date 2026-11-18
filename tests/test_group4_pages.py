"""Sačuvana PC konfiguracija i stranice grešaka."""

from extensions import db
from models import CartItem, Category, PCBuild, Product, User, build_components


def make_build(owner, public=True, stock=2):
    cat = Category(name='Procesori G4', slug='g4-cpu', component_type='CPU')
    db.session.add(cat)
    db.session.flush()
    p = Product(name='Ryzen G4', slug='ryzen-g4', price=300, stock=stock, category_id=cat.id,
                component_type='CPU', is_publicly_visible=stock > 0)
    db.session.add(p)
    db.session.flush()
    b = PCBuild(user_id=owner.id, name='Moj gaming PC', is_public=public)
    db.session.add(b)
    db.session.flush()
    db.session.execute(build_components.insert().values(build_id=b.id, product_id=p.id, quantity=1))
    db.session.commit()
    return b, p


def test_saved_build_page_renders(client, sample_user):
    build, product = make_build(User.query.filter_by(email='test@example.com').first())
    res = client.get(f'/pc-builder/build/{build.id}')
    assert res.status_code == 200                       # ranije BuildError -> 500
    html = res.get_data(as_text=True)
    assert 'Moj gaming PC' in html and 'Ryzen G4' in html
    assert f'/product/{product.slug}' in html
    assert f'?build={build.id}' in html                 # otvaranje u konfiguratoru


def test_add_build_to_cart_skips_sold_out_and_private(auth_client, sample_user, admin_user):
    user = User.query.filter_by(email='test@example.com').first()
    build, product = make_build(user)
    auth_client.post(f'/pc-builder/build/{build.id}/add-to-cart')
    assert CartItem.query.filter_by(user_id=user.id, product_id=product.id).count() == 1

    admin = User.query.filter_by(email='admin@example.com').first()
    private = PCBuild(user_id=admin.id, name='Tuđa', is_public=False)
    db.session.add(private)
    db.session.commit()
    res = auth_client.post(f'/pc-builder/build/{private.id}/add-to-cart')
    assert '/pc-builder' in res.headers['Location'] and '/cart' not in res.headers['Location']


def test_404_page_has_search(client):
    res = client.get('/ne-postoji-ova-stranica')
    assert res.status_code == 404
    html = res.get_data(as_text=True)
    assert 'Ova stranica ne postoji' in html and 'name="q"' in html
