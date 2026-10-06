"""Tests for the lager ↔ site sync admin page (/admin/lager-sync)."""

import pytest

from extensions import db
from models import Product, Category, LagerProduct, LagerCategory
from routes.admin.lager_sync_routes import target_price, name_similarity, best_name_match, DUPLICATE_MIN_SCORE


# =============================================================================
# Helpers
# =============================================================================

def make_lager_tree():
    main = LagerCategory(name='CPU', slug='l-cpu')
    other_main = LagerCategory(name='MONITORI', slug='l-monitori')
    db.session.add_all([main, other_main])
    db.session.flush()
    sub = LagerCategory(name='AMD', slug='l-cpu-amd', parent_id=main.id)
    db.session.add(sub)
    db.session.flush()
    return main, sub, other_main


def make_product(name, slug, price, stock, category, lager=None):
    product = Product(name=name, slug=slug, price=price, stock=stock, category_id=category.id,
                      is_publicly_visible=stock > 0, lager_product_id=lager.id if lager else None)
    db.session.add(product)
    return product


@pytest.fixture
def site_category(app):
    category = Category(name='Procesori', slug='sync-procesori')
    db.session.add(category)
    db.session.commit()
    return category


# =============================================================================
# Pure helpers
# =============================================================================

class TestTargetPrice:
    def test_rounds_up_to_next_whole_number(self):
        assert target_price(161, 5) == 170   # 169.05 -> 170
        assert target_price(18, 5) == 19     # 18.90 -> 19

    def test_exact_value_is_not_bumped_by_float_error(self):
        # 100 * 1.05 == 105.00000000000001 in floating point
        assert target_price(100, 5) == 105
        assert target_price(120, 5) == 126

    def test_missing_purchase_price(self):
        assert target_price(None, 5) is None
        assert target_price(0, 5) is None


class TestMatching:
    def test_similarity_ignores_case_and_spacing(self):
        assert name_similarity('GIGABYTE GP-P650SS 650W  ICE white',
                               'gigabyte gp-p650ss 650w ice white') == 1.0

    def test_best_match_requires_minimum_score(self):
        items = [LagerProduct(name='ASUS A31 PLUS TG ARGB BIJELO'), LagerProduct(name='DEEPCOOL PF750 750W')]
        assert best_name_match('ASUS A31 PLUS TG BIJELO', items).name == 'ASUS A31 PLUS TG ARGB BIJELO'
        assert best_name_match('KINGSTON FURY 32GB', items) is None

    def test_duplicate_threshold(self):
        site = [Product(name='AMD Ryzen 3 4100 3.80GHz AM4 BOX + Wraith Cooler'),
                Product(name='GIGABYTE A620M GAMING X')]
        assert best_name_match('AMD AM4 BOX Wraith Stealth cooler', site, DUPLICATE_MIN_SCORE) is None
        assert best_name_match('GIGABYTE A620M GAMING X - OPEN BOX', site, DUPLICATE_MIN_SCORE) is site[1]


# =============================================================================
# Routes
# =============================================================================

class TestLagerSyncPage:
    def test_requires_admin(self, auth_client):
        response = auth_client.get('/admin/lager-sync', follow_redirects=False)
        assert response.status_code == 302

    def test_lists_mismatches_and_unpublished_stock(self, admin_client, site_category):
        main, sub, other_main = make_lager_tree()
        linked = LagerProduct(name='AMD Ryzen 5 5500', stock=2, purchase_price=161, category_id=sub.id)
        unpublished = LagerProduct(name='AMD Ryzen 7 7700X', stock=1, purchase_price=477, category_id=sub.id)
        sold_out = LagerProduct(name='AMD Ryzen 5 3600', stock=0, purchase_price=139, category_id=sub.id)
        unrelated = LagerProduct(name='Monitor 24"', stock=3, purchase_price=200, category_id=other_main.id)
        db.session.add_all([linked, unpublished, sold_out, unrelated])
        db.session.flush()
        make_product('AMD Ryzen 5 5500 BOX', 'sync-r5-5500', 169, 1, site_category, lager=linked)
        db.session.commit()

        html = admin_client.get('/admin/lager-sync').get_data(as_text=True)

        assert 'AMD Ryzen 5 5500 BOX' in html
        assert '170 KM' in html                  # target price shown for the mismatch
        assert 'AMD Ryzen 7 7700X' in html       # in stock, not published
        assert '501 KM' in html                  # 477 * 1.05 = 500.85 -> 501
        assert 'AMD Ryzen 5 3600' not in html    # out of stock on lager
        assert 'Monitor 24' not in html          # lager category with no site products


class TestApplySync:
    def test_apply_all_sets_stock_price_and_visibility(self, admin_client, site_category):
        _, sub, _ = make_lager_tree()
        restocked = LagerProduct(name='R5 5500', stock=3, purchase_price=161, category_id=sub.id)
        sold_out = LagerProduct(name='R5 3600', stock=0, purchase_price=139, category_id=sub.id)
        db.session.add_all([restocked, sold_out])
        db.session.flush()
        a = make_product('R5 5500 site', 'sync-a', 150, 0, site_category, lager=restocked)
        b = make_product('R5 3600 site', 'sync-b', 146, 2, site_category, lager=sold_out)
        untouched = make_product('Unlinked', 'sync-c', 99, 4, site_category)
        db.session.commit()
        ids = (a.id, b.id, untouched.id)

        response = admin_client.post('/admin/lager-sync/apply-all', data={'markup': '5'})
        assert response.status_code == 302

        db.session.expire_all()
        a, b, untouched = (db.session.get(Product, i) for i in ids)
        assert (a.stock, a.price, a.is_publicly_visible) == (3, 170, True)
        assert (b.stock, b.price, b.is_publicly_visible) == (0, 146, False)
        assert (untouched.stock, untouched.price) == (4, 99)

    def test_apply_single_respects_markup(self, admin_client, site_category):
        _, sub, _ = make_lager_tree()
        item = LagerProduct(name='Cooler', stock=1, purchase_price=75, category_id=sub.id)
        db.session.add(item)
        db.session.flush()
        product = make_product('Cooler site', 'sync-cooler', 75, 1, site_category, lager=item)
        db.session.commit()

        admin_client.post(f'/admin/lager-sync/apply/{product.id}', data={'markup': '10'})

        db.session.expire_all()
        assert db.session.get(Product, product.id).price == 83  # 82.50 -> 83


class TestLinking:
    def test_link_and_unlink(self, admin_client, site_category):
        _, sub, _ = make_lager_tree()
        item = LagerProduct(name='Hyper 212', stock=1, purchase_price=38, category_id=sub.id)
        db.session.add(item)
        db.session.flush()
        product = make_product('COOLERMASTER Hyper 212', 'sync-hyper', 38, 3, site_category)
        db.session.commit()
        product_id, item_id = product.id, item.id

        admin_client.post(f'/admin/lager-sync/link/{product_id}',
                          data={'lager_ref': f'Hyper 212 (kol. 1) #{item_id}'})
        db.session.expire_all()
        assert db.session.get(Product, product_id).lager_product_id == item_id

        admin_client.post(f'/admin/lager-sync/link/{product_id}', data={'lager_ref': ''})
        db.session.expire_all()
        assert db.session.get(Product, product_id).lager_product_id is None

    def test_link_rejects_free_text(self, admin_client, site_category):
        product = make_product('Something', 'sync-free', 10, 1, site_category)
        db.session.commit()

        admin_client.post(f'/admin/lager-sync/link/{product.id}', data={'lager_ref': 'Hyper 212'})

        db.session.expire_all()
        assert db.session.get(Product, product.id).lager_product_id is None

    def test_auto_link_only_unique_exact_names(self, admin_client, site_category):
        _, sub, _ = make_lager_tree()
        unique = LagerProduct(name='DEEPCOOL PF750 750W', stock=0, category_id=sub.id)
        dup_a = LagerProduct(name='AMD Ryzen 7 5700X BOX', stock=0, category_id=sub.id)
        dup_b = LagerProduct(name='AMD Ryzen 7 5700X BOX', stock=0, category_id=sub.id)
        db.session.add_all([unique, dup_a, dup_b])
        db.session.flush()
        exact = make_product('deepcool  PF750 750W', 'sync-pf750', 109, 0, site_category)
        ambiguous = make_product('AMD Ryzen 7 5700X BOX', 'sync-5700x', 294, 0, site_category)
        fuzzy = make_product('DEEPCOOL PF750', 'sync-pf750-short', 109, 0, site_category)
        db.session.commit()
        ids = (exact.id, ambiguous.id, fuzzy.id)
        unique_id = unique.id

        admin_client.post('/admin/lager-sync/auto-link')

        db.session.expire_all()
        exact, ambiguous, fuzzy = (db.session.get(Product, i) for i in ids)
        assert exact.lager_product_id == unique_id
        assert ambiguous.lager_product_id is None
        assert fuzzy.lager_product_id is None


class TestPublishFromLager:
    def _setup(self, site_category):
        _, sub, _ = make_lager_tree()
        published = LagerProduct(name='AMD Ryzen 5 5500', stock=1, purchase_price=161, category_id=sub.id)
        new_item = LagerProduct(name='AMD Ryzen 7 7700X AM5 BOX', stock=2, purchase_price=477, category_id=sub.id)
        open_box = LagerProduct(name='GIGABYTE A620M GAMING X - OPEN BOX', stock=1, purchase_price=185,
                                category_id=sub.id)
        db.session.add_all([published, new_item, open_box])
        db.session.flush()
        make_product('AMD Ryzen 5 5500 BOX', 'pub-r5', 170, 1, site_category, lager=published)
        db.session.commit()
        return new_item.id, open_box.id

    def test_add_form_is_prefilled_from_lager(self, admin_client, site_category):
        new_id, _ = self._setup(site_category)

        html = admin_client.get(f'/admin/products/add?lager_id={new_id}').get_data(as_text=True)

        assert 'Objavljujete artikal sa lagera' in html
        assert 'value="AMD Ryzen 7 7700X AM5 BOX"' in html
        assert 'value="501.0"' in html                      # 477 * 1.05 = 500.85 -> 501
        assert 'value="2"' in html                          # stock
        assert f'<option selected value="{site_category.id}">' in html  # guessed from linked sibling
        assert f'value="{new_id}"' in html                  # hidden lager_product_id

    def test_open_box_is_prefilled_as_used(self, admin_client, site_category):
        _, open_box_id = self._setup(site_category)

        html = admin_client.get(f'/admin/products/add?lager_id={open_box_id}').get_data(as_text=True)

        assert '<option selected value="Polovno">' in html

    def test_saving_links_product_to_lager(self, admin_client, site_category):
        new_id, _ = self._setup(site_category)

        response = admin_client.post('/admin/products/add', data={
            'name': 'AMD Ryzen 7 7700X AM5 BOX',
            'description': 'Opis',
            'price': '501',
            'stock': '2',
            'category_id': str(site_category.id),
            'condition': 'Novo',
            'availability': 'Dostupno odmah',
            'lager_product_id': str(new_id),
        })

        assert response.status_code == 302
        assert '/admin/lager-sync' in response.headers['Location']
        product = Product.query.filter_by(name='AMD Ryzen 7 7700X AM5 BOX').one()
        assert product.lager_product_id == new_id
        assert product.is_publicly_visible

    def test_sync_page_warns_about_similar_unlinked_product(self, admin_client, site_category):
        _, open_box_id = self._setup(site_category)
        make_product('GIGABYTE A620M GAMING X', 'pub-a620', 241, 0, site_category)
        db.session.commit()

        html = admin_client.get('/admin/lager-sync').get_data(as_text=True)

        assert f'/admin/products/add?lager_id={open_box_id}' in html
        assert 'Možda već postoji' in html


class TestProductListReturnsToSameTab:
    def _post_edit(self, client, product, next_url):
        return client.post(f'/admin/products/edit/{product.id}?next={next_url}', data={
            'name': product.name, 'description': 'Opis', 'price': '10', 'stock': '1',
            'category_id': str(product.category_id), 'condition': 'Novo', 'availability': 'Dostupno odmah',
        })

    def test_edit_returns_to_previous_list_view(self, admin_client, site_category):
        product = make_product('Tab test', 'tab-test', 10, 1, site_category)
        db.session.commit()
        back = f'/admin/products?category_id={site_category.id}%26page=2'

        response = self._post_edit(admin_client, product, back)

        assert response.status_code == 302
        assert response.headers['Location'].endswith(f'/admin/products?category_id={site_category.id}&page=2')

    def test_edit_ignores_foreign_next(self, admin_client, site_category):
        product = make_product('Tab test 2', 'tab-test-2', 10, 1, site_category)
        db.session.commit()

        response = self._post_edit(admin_client, product, 'https://evil.example/admin/products')

        assert response.headers['Location'].endswith('/admin/products')

    def test_list_links_carry_current_view(self, admin_client, site_category):
        product = make_product('Tab test 3', 'tab-test-3', 10, 1, site_category)
        db.session.commit()

        html = admin_client.get(f'/admin/products?category_id={site_category.id}').get_data(as_text=True)

        assert f'/admin/products/edit/{product.id}?next=/admin/products?category_id%3D{site_category.id}' in html
