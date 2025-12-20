from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from extensions import db
from models import LagerProduct, LagerCategory, User
from functools import wraps
import re

# Kreiranje novog blueprinta za lager
lager_bp = Blueprint('lager', __name__, url_prefix='/lager')


# Helper for slugify
def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[\s-]+', '-', s)
    s = re.sub(r'[^\w-]', '', s)
    return s


# Kreiranje dekoratora za proveru uloga
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Nemate dozvolu.'}), 403
                flash('Nemate dozvolu za pristup ovoj stranici.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)

        return decorated_function

    return wrapper


# Definisanje uloga u obe varijante (mala i velika slova) radi rešavanja problema sa osetljivošću na velika slova
FULL_ACCESS_ROLES = ('admin', 'dobavljac', 'Admin', 'Dobavljač')
VIEW_ACCESS_ROLES = ('admin', 'dobavljac', 'distributer', 'Admin', 'Dobavljač', 'Distributer')


@lager_bp.route('/')
@login_required
@role_required(*VIEW_ACCESS_ROLES)
def view_lager():
    # NOVO: Dohvatanje aktivnog taba iz query parametra
    active_tab = request.args.get('active_tab', 'Vrednost_Lagera')  # Vrednost_Lagera je default

    # NOVO: Dohvatanje filtera za nulte zalihe i pretrage
    show_zero_stock = request.args.get('show_zero', 'false').lower() == 'true'
    search_query = request.args.get('search', '').strip().lower()

    main_categories = LagerCategory.query.filter(LagerCategory.parent_id.is_(None)).order_by(
        LagerCategory.sort_order).all()

    lager_data = {}
    stock_values = {'grand_total': 0, 'categories': {}}
    all_categories_for_js = {cat.name: [sub.name for sub in sorted(cat.subcategories, key=lambda s: s.sort_order)] for
                             cat in main_categories}

    all_products = LagerProduct.query.order_by(LagerProduct.name).all()
    products_by_cat_id = {}
    for p in all_products:
        cat_id = p.category_id
        if cat_id not in products_by_cat_id:
            products_by_cat_id[cat_id] = []
        products_by_cat_id[cat_id].append(p)

    for category in main_categories:
        current_main_category_data = {}
        category_total_value = 0

        child_categories = sorted(category.subcategories, key=lambda s: s.sort_order)
        for subcat in child_categories:
            products_in_subcat = products_by_cat_id.get(subcat.id, [])

            # NOVO: Primena filtera za nulte zalihe i pretragu
            if current_user.role.lower() == 'distributer':
                products_in_subcat = [p for p in products_in_subcat if p.stock > 0]
            elif not show_zero_stock:
                products_in_subcat = [p for p in products_in_subcat if p.stock > 0]

            # NOVO: Primena pretrage
            if search_query:
                products_in_subcat = [p for p in products_in_subcat if search_query in p.name.lower()]

            if products_in_subcat:
                current_main_category_data[subcat.name] = products_in_subcat
                for p in products_in_subcat:
                    category_total_value += (p.purchase_price or 0) * (p.stock or 0)

        products_in_main = products_by_cat_id.get(category.id, [])

        # NOVO: Primena filtera za nulte zalihe i pretragu
        if current_user.role.lower() == 'distributer':
            products_in_main = [p for p in products_in_main if p.stock > 0]
        elif not show_zero_stock:
            products_in_main = [p for p in products_in_main if p.stock > 0]

        # NOVO: Primena pretrage
        if search_query:
            products_in_main = [p for p in products_in_main if search_query in p.name.lower()]

        if products_in_main:
            current_main_category_data[category.name] = products_in_main
            for p in products_in_main:
                category_total_value += (p.purchase_price or 0) * (p.stock or 0)

        # --- KLJUČNA IZMJENA ---
        # Uvijek dodajemo glavnu kategoriju u podatke za prikaz, čak i ako je prazna.
        # Templejt će se pobrinuti za prikaz praznog taba sa dugmićima za dodavanje.
        lager_data[category.name] = current_main_category_data

        # Vrijednost zaliha dodajemo samo ako zaista postoji.
        if category_total_value > 0:
            stock_values['categories'][category.name] = category_total_value
            stock_values['grand_total'] += category_total_value

    # --- NOVI DIO ---
    # Dobavi ID-jeve 10 posljednje ažuriranih artikala (bilo dodavanje ili izmjena)
    try:
        recent_items_query = db.session.query(LagerProduct.id).order_by(LagerProduct.updated_at.desc()).limit(10).all()
        # Kreiraj set ID-jeva za brzu provjeru u template-u
        recent_item_ids = {item[0] for item in recent_items_query}
    except Exception as e:
        print(f"Greška prilikom dobavljanja nedavnih artikala: {e}")
        recent_item_ids = set()  # U slučaju greške, proslijedi prazan set
    # --- KRAJ NOVOG DIJELA ---

    return render_template('lager.html',
                           title='Interaktivni Lager',
                           data=lager_data,
                           stock_values=stock_values,
                           current_user_role=current_user.role,
                           lager_category_data_for_js=all_categories_for_js,
                           active_tab=active_tab,
                           recent_item_ids=recent_item_ids,
                           show_zero_stock=show_zero_stock,  # NOVO: Prosleđivanje stanja filtera
                           search_query=search_query)  # NOVO: Prosleđivanje pretrage


# --- Ostatak fajla ostaje nepromijenjen, osim rute update_details, add_product i add_subcategory ---

@lager_bp.route('/update_stock', methods=['POST'])
@login_required
@role_required(*FULL_ACCESS_ROLES)
def update_stock():
    data = request.get_json()
    product_id = data.get('product_id')
    change = data.get('change')
    if not all([product_id, isinstance(change, int)]):
        return jsonify({'success': False, 'message': 'Nevažeći podaci.'}), 400
    product = LagerProduct.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Proizvod nije pronađen.'}), 404
    product.stock = max(0, product.stock + change)
    db.session.commit()
    return jsonify({'success': True, 'new_stock': product.stock})


@lager_bp.route('/update_note', methods=['POST'])
@login_required
@role_required(*VIEW_ACCESS_ROLES)
def update_note():
    data = request.get_json()
    product_id = data.get('product_id')
    note_type = data.get('note_type')
    note_value = data.get('note_value', '')
    if not all([product_id, note_type in ['internal_note', 'reservation_note']]):
        return jsonify({'success': False, 'message': 'Nevažeći podaci.'}), 400
    product = LagerProduct.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Proizvod nije pronađen.'}), 404
    if note_type == 'internal_note':
        product.internal_note = note_value
    elif note_type == 'reservation_note':
        product.reservation_note = note_value
    db.session.commit()
    return jsonify({'success': True, 'message': 'Napomena je sačuvana.'})


@lager_bp.route('/update_details/<int:product_id>', methods=['POST'])
@login_required
@role_required(*VIEW_ACCESS_ROLES)
def update_details(product_id):
    product = LagerProduct.query.get_or_404(product_id)
    user_role = current_user.role.lower()

    # NOVO: Dohvatanje imena aktivnog taba iz forme
    active_tab_slug = request.form.get('active_tab_slug', None)

    # Distributer ima poseban set dozvola za beleške
    if user_role == 'distributer':
        product.reservation_note = request.form.get('reservation_note', product.reservation_note)
        product.internal_note = request.form.get('internal_note', product.internal_note)

    # Admin i Dobavljač (koji sada imaju iste dozvole)
    if user_role in ['admin', 'dobavljac']:
        try:
            # Omogući Adminu i Dobavljaču da mijenjaju naziv artikla
            product_name = request.form.get('product_name', '').strip()
            if product_name:
                product.name = product_name

            product.stock = int(request.form.get('stock', product.stock))
            price_str = request.form.get('purchase_price', str(product.purchase_price or 0.0)).replace(',', '.')
            product.purchase_price = float(price_str)
            product.for_company = 'for_company' in request.form
            product.internal_note = request.form.get('internal_note', product.internal_note)

            # Omogući Dobavljaču da menja reservation_note (kao i Adminu)
            product.reservation_note = request.form.get('reservation_note', product.reservation_note)

        except (ValueError, TypeError):
            flash('Neispravan format za količinu ili cijenu.', 'danger')
            # NOVO: Redirekcija na isti tab u slučaju greške
            if active_tab_slug:
                return redirect(url_for('lager.view_lager', active_tab=active_tab_slug))
            return redirect(url_for('lager.view_lager'))

    try:
        db.session.commit()
        flash(f'Proizvod "{product.name}" je uspješno ažuriran.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Došlo je do greške prilikom ažuriranja: {str(e)}', 'danger')

    # NOVO: Redirekcija na isti tab
    if active_tab_slug:
        return redirect(url_for('lager.view_lager', active_tab=active_tab_slug))

    return redirect(url_for('lager.view_lager'))


@lager_bp.route('/add_product', methods=['POST'])
@login_required
@role_required(*FULL_ACCESS_ROLES)
def add_product():
    # NOVO: Inicijalizacija category_name za redirekciju
    category_name_for_redirect = None
    try:
        product_name = request.form.get('product_name', '').strip()
        subcategory_name = request.form.get('subcategory_name', '').strip()
        category_name = request.form.get('category_name', '').strip()
        category_name_for_redirect = category_name  # Postavljamo vrednost pre validacije

        if not product_name:
            flash('Naziv proizvoda je obavezan.', 'danger')
            # NOVO: Redirekcija na isti tab u slučaju greške
            if category_name_for_redirect:
                tab_slug = category_name_for_redirect.replace(' ', '_').replace('/', '_')
                return redirect(url_for('lager.view_lager', active_tab=tab_slug))
            return redirect(url_for('lager.view_lager'))

        category = None
        if subcategory_name:
            parent_category = LagerCategory.query.filter_by(name=category_name).first()
            if not parent_category:
                flash(f'Glavna kategorija "{category_name}" nije pronađena.', 'danger')
                if category_name_for_redirect:
                    tab_slug = category_name_for_redirect.replace(' ', '_').replace('/', '_')
                    return redirect(url_for('lager.view_lager', active_tab=tab_slug))
                return redirect(url_for('lager.view_lager'))

            category = LagerCategory.query.filter_by(name=subcategory_name, parent_id=parent_category.id).first()
            if not category:
                flash(f'Podkategorija "{subcategory_name}" unutar "{category_name}" nije pronađena.', 'danger')
                if category_name_for_redirect:
                    tab_slug = category_name_for_redirect.replace(' ', '_').replace('/', '_')
                    return redirect(url_for('lager.view_lager', active_tab=tab_slug))
                return redirect(url_for('lager.view_lager'))
        else:
            category = LagerCategory.query.filter_by(name=category_name).first()
            if not category:
                flash(f'Kategorija "{category_name}" nije pronađena.', 'danger')
                if category_name_for_redirect:
                    tab_slug = category_name_for_redirect.replace(' ', '_').replace('/', '_')
                    return redirect(url_for('lager.view_lager', active_tab=tab_slug))
                return redirect(url_for('lager.view_lager'))

        stock = int(request.form.get('stock', 0))
        purchase_price_str = request.form.get('purchase_price', '0').replace(',', '.')
        purchase_price = float(purchase_price_str)
        for_company = 'for_company' in request.form
        internal_note = request.form.get('internal_note', '').strip()

        new_product = LagerProduct(
            name=product_name, stock=stock, purchase_price=purchase_price,
            for_company=for_company, internal_note=internal_note if internal_note else None,
            category_id=category.id
        )
        db.session.add(new_product)
        db.session.commit()

        category_info = f' u kategoriju "{category.name}"'
        if category.parent_id:
            parent = LagerCategory.query.get(category.parent_id)
            if parent:
                category_info = f' u {parent.name} > {category.name}'

        flash(f'Proizvod "{product_name}" je uspješno dodat{category_info}!', 'success')
    except ValueError:
        flash('Neispravan format za količinu ili cijenu.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Došlo je do greške prilikom dodavanja proizvoda: {str(e)}', 'danger')

    # NOVO: Redirekcija na isti tab
    if category_name_for_redirect:
        tab_slug = category_name_for_redirect.replace(' ', '_').replace('/', '_')
        return redirect(url_for('lager.view_lager', active_tab=tab_slug))

    return redirect(url_for('lager.view_lager'))


@lager_bp.route('/add_subcategory', methods=['POST'])
@login_required
@role_required(*FULL_ACCESS_ROLES)
def add_subcategory():
    parent_category_name = request.form.get('parent_category_name')
    parent_category_slug = parent_category_name.replace(' ', '_').replace('/', '_')  # Slug za redirekciju
    subcategory_name = request.form.get('subcategory_name', '').strip()

    if not subcategory_name or not parent_category_name:
        flash('Naziv podkategorije je obavezan.', 'danger')
        # NOVO: Redirekcija na isti tab u slučaju greške
        return redirect(url_for('lager.view_lager', active_tab=parent_category_slug))

    parent_category = LagerCategory.query.filter_by(name=parent_category_name).first()
    if not parent_category:
        flash(f'Glavna kategorija "{parent_category_name}" nije pronađena.', 'danger')
        return redirect(url_for('lager.view_lager', active_tab=parent_category_slug))

    # Provjera da li podkategorija sa tim imenom vec postoji pod istim roditeljem
    existing_category = LagerCategory.query.filter_by(name=subcategory_name, parent_id=parent_category.id).first()
    if existing_category:
        flash(f'Podkategorija "{subcategory_name}" već postoji u "{parent_category.name}".', 'warning')
        return redirect(url_for('lager.view_lager', active_tab=parent_category_slug))

    new_slug = slugify(subcategory_name)
    counter = 1
    unique_slug = new_slug
    while LagerCategory.query.filter_by(slug=unique_slug).first():
        unique_slug = f"{new_slug}-{counter}"
        counter += 1

    new_subcategory = LagerCategory(
        name=subcategory_name, slug=unique_slug, parent_id=parent_category.id
    )
    try:
        db.session.add(new_subcategory)
        db.session.commit()
        flash(f'Podkategorija "{subcategory_name}" je uspješno dodata u "{parent_category_name}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Došlo je do greške: {str(e)}', 'danger')

    # NOVO: Redirekcija na isti tab
    return redirect(url_for('lager.view_lager', active_tab=parent_category_slug))