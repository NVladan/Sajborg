"""Usklađivanje objavljenih proizvoda sa lagerom.

Lager je izvor istine: stanje proizvoda na sajtu treba da bude jednako stanju
povezanog artikla na lageru, a cijena jednaka lagerskoj prodajnoj cijeni
(nabavna + marža), zaokruženoj na prvi veći cijeli broj.
"""
import math
import re
from collections import Counter

from flask import render_template, redirect, url_for, flash, request
from sqlalchemy.orm import joinedload

from extensions import db
from models import Product, LagerProduct, LagerCategory
from . import admin_bp, admin_required

DEFAULT_MARKUP = 5  # isti default kao "Uvećaj cijenu" na stranici lagera
SUGGESTION_MIN_SCORE = 0.5
DUPLICATE_MIN_SCORE = 0.6  # strožije: upozorenje "možda već postoji" ne smije lažno uzbunjivati
LAGER_REF_RE = re.compile(r'#(\d+)\s*$')


def target_price(purchase_price, markup=DEFAULT_MARKUP):
    """Prodajna cijena sa lagera zaokružena naviše; None ako nema nabavne cijene."""
    if not purchase_price or purchase_price <= 0:
        return None
    # Zaokruživanje na 2 decimale prije ceil, da 100 * 1.05 = 105.00000000000001 ne postane 106
    return float(math.ceil(round(purchase_price * (1 + markup / 100), 2)))


def normalize_name(name):
    return ' '.join((name or '').lower().split())


def _tokens(name):
    return set(re.findall(r'[a-z0-9]+(?:[.\-/][a-z0-9]+)*', normalize_name(name)))


def name_similarity(a, b):
    """Jaccard sličnost riječi u nazivima (0..1)."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def best_name_match(name, candidates, min_score=SUGGESTION_MIN_SCORE):
    """Kandidat (proizvod ili artikal na lageru) najsličnijeg naziva, ili None."""
    best, best_score = None, 0.0
    for item in candidates:
        score = name_similarity(name, item.name)
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= min_score else None


def lager_label(item):
    return f'{item.name} (kol. {item.stock or 0}) #{item.id}'


def main_category(category):
    return category.parent if category and category.parent else category


TABS = ('uskladi', 'objavi', 'povezi', 'uredu')


def _back(markup):
    """Nazad na stranicu, na tab sa kojeg je akcija pokrenuta."""
    tab = request.form.get('tab')
    return redirect(url_for('admin.lager_sync', markup=markup, _anchor=tab if tab in TABS else None))


def _parse_markup(value):
    try:
        markup = float(value)
    except (TypeError, ValueError):
        return DEFAULT_MARKUP
    return min(max(markup, 0), 100)


def guess_site_category_id(lager_item):
    """Kategorija na sajtu u kojoj su već objavljeni artikli iz iste (pod)kategorije lagera."""
    linked = (Product.query
              .options(joinedload(Product.lager_product).joinedload(LagerProduct.category))
              .filter(Product.lager_product_id.isnot(None))
              .all())
    same_sub = Counter(p.category_id for p in linked if p.lager_product.category_id == lager_item.category_id)
    if same_sub:
        return same_sub.most_common(1)[0][0]
    main = main_category(lager_item.category)
    same_main = Counter(p.category_id for p in linked if main_category(p.lager_product.category).id == main.id)
    return same_main.most_common(1)[0][0] if same_main else None


def is_used_item(lager_item):
    main = main_category(lager_item.category)
    return 'open box' in lager_item.name.lower() or main.name.upper().startswith('POLOVN')


def prefill_product_form(form, lager_item, markup=DEFAULT_MARKUP):
    """Popunjava formu za novi proizvod podacima sa lagera (samo pri GET)."""
    form.lager_product_id.data = str(lager_item.id)
    form.name.data = lager_item.name
    form.description.data = lager_item.name
    form.stock.data = lager_item.stock or 0
    form.price.data = target_price(lager_item.purchase_price, markup)
    form.condition.data = 'Polovno' if is_used_item(lager_item) else 'Novo'
    category_id = guess_site_category_id(lager_item)
    if category_id:
        form.category_id.data = category_id


def sync_diff(product, markup):
    """Vraća (željeno_stanje, željena_cijena) ili None ako je proizvod usklađen."""
    lager = product.lager_product
    want_stock = lager.stock or 0
    want_price = target_price(lager.purchase_price, markup)
    stock_differs = product.stock != want_stock
    price_differs = want_price is not None and product.price != want_price
    if stock_differs or price_differs:
        return want_stock, want_price
    return None


def apply_sync(product, markup):
    """Postavlja stanje i cijenu proizvoda prema lageru. Vraća True ako je nešto promijenjeno."""
    diff = sync_diff(product, markup)
    if diff is None:
        return False
    want_stock, want_price = diff
    product.stock = want_stock
    if want_price is not None:
        product.price = want_price
    product.is_publicly_visible = want_stock > 0
    return True


@admin_bp.route('/lager-sync')
@admin_required
def lager_sync():
    markup = _parse_markup(request.args.get('markup', DEFAULT_MARKUP))

    products = (Product.query
                .options(joinedload(Product.lager_product), joinedload(Product.category))
                .order_by(Product.name)
                .all())
    lager_items = (LagerProduct.query
                   .options(joinedload(LagerProduct.category).joinedload(LagerCategory.parent))
                   .order_by(LagerProduct.name)
                   .all())

    linked = [p for p in products if p.lager_product]
    mismatched = []
    in_sync = []
    for p in linked:
        diff = sync_diff(p, markup)
        if diff is None:
            in_sync.append(p)
        else:
            mismatched.append({'product': p, 'want_stock': diff[0], 'want_price': diff[1]})

    linked_lager_ids = {p.lager_product_id for p in linked}
    unlinked = sorted((p for p in products if not p.lager_product),
                      key=lambda p: (p.stock <= 0, p.name.lower()))
    unlinked_rows = [{'product': p, 'suggestion': best_name_match(p.name, lager_items)} for p in unlinked]

    # Nepovezana roba sa lagera, samo iz glavnih kategorija koje već imaju bar jedan povezan artikal
    relevant_main_ids = {main_category(p.lager_product.category).id for p in linked}
    unpublished = {}
    for item in lager_items:
        if (item.stock or 0) <= 0 or item.id in linked_lager_ids:
            continue
        main = main_category(item.category)
        if relevant_main_ids and main.id not in relevant_main_ids:
            continue
        unpublished.setdefault(main.name, []).append({
            'item': item,
            'sale_price': target_price(item.purchase_price, markup),
            # Možda proizvod već postoji na sajtu (npr. skriven sa stanjem 0) — bolje ga povezati nego duplirati
            'similar_product': best_name_match(item.name, unlinked, DUPLICATE_MIN_SCORE),
        })

    return render_template('admin/lager_sync.html',
                           title='Lager ↔ Sajt',
                           markup=markup,
                           mismatched=mismatched,
                           in_sync=in_sync,
                           unlinked_rows=unlinked_rows,
                           unpublished=unpublished,
                           filtered_by_links=bool(relevant_main_ids),
                           lager_items=lager_items,
                           lager_label=lager_label)


@admin_bp.route('/lager-sync/apply/<int:product_id>', methods=['POST'])
@admin_required
def lager_sync_apply(product_id):
    markup = _parse_markup(request.form.get('markup'))
    product = Product.query.get_or_404(product_id)
    if not product.lager_product:
        flash('Proizvod nije povezan sa lagerom.', 'warning')
    elif apply_sync(product, markup):
        db.session.commit()
        flash(f'Usklađeno: {product.name}', 'success')
    else:
        flash(f'{product.name} je već usklađen.', 'info')
    return _back(markup)


@admin_bp.route('/lager-sync/apply-all', methods=['POST'])
@admin_required
def lager_sync_apply_all():
    markup = _parse_markup(request.form.get('markup'))
    products = Product.query.filter(Product.lager_product_id.isnot(None)).all()
    changed = sum(1 for p in products if apply_sync(p, markup))
    db.session.commit()
    flash(f'Usklađeno proizvoda: {changed}.', 'success')
    return _back(markup)


@admin_bp.route('/lager-sync/link/<int:product_id>', methods=['POST'])
@admin_required
def lager_sync_link(product_id):
    markup = _parse_markup(request.form.get('markup'))
    product = Product.query.get_or_404(product_id)
    ref = (request.form.get('lager_ref') or '').strip()

    if not ref:
        product.lager_product_id = None
        db.session.commit()
        flash(f'Odvezano od lagera: {product.name}', 'info')
        return _back(markup)

    match = LAGER_REF_RE.search(ref)
    lager_item = db.session.get(LagerProduct, int(match.group(1))) if match else None
    if not lager_item:
        flash('Izaberite artikal sa lagera iz liste.', 'danger')
        return _back(markup)

    product.lager_product_id = lager_item.id
    db.session.commit()
    flash(f'Povezano: {product.name} → {lager_item.name}', 'success')
    return _back(markup)


@admin_bp.route('/lager-sync/auto-link', methods=['POST'])
@admin_required
def lager_sync_auto_link():
    """Povezuje nepovezane proizvode čiji naziv je identičan tačno jednom artiklu na lageru."""
    markup = _parse_markup(request.form.get('markup'))
    by_name = {}
    for item in LagerProduct.query.all():
        by_name.setdefault(normalize_name(item.name), []).append(item)

    linked = 0
    for product in Product.query.filter(Product.lager_product_id.is_(None)).all():
        candidates = by_name.get(normalize_name(product.name), [])
        if len(candidates) == 1:
            product.lager_product_id = candidates[0].id
            linked += 1
    db.session.commit()
    flash(f'Automatski povezano proizvoda: {linked}.', 'success')
    return _back(markup)
