from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from extensions import db, csrf
from models import Product, PCBuild, build_components, ProductAttributeValue, Category
from forms.builder_forms import PCBuildForm, AddToCartForm
from utils import check_pc_build_compatibility
from pc_build_check import SLOTS, analyze_build

builder_bp = Blueprint('builder', __name__, url_prefix='/pc-builder')

@builder_bp.route('/')
def builder():
    available = {c[0] for c in db.session.query(Product.component_type)
                 .filter(Product.component_type.isnot(None), Product.stock > 0).distinct().all() if c[0]}
    # Slika slota = slika kategorije prodavnice sa tim tipom komponente (glavna kategorija ima prednost)
    images = {}
    for cat in Category.query.filter(Category.component_type.isnot(None)).order_by(Category.parent_id.isnot(None)).all():
        if cat.image_path and cat.component_type not in images:
            images[cat.component_type] = url_for('static', filename=cat.image_path)
    slots = [{'type': key, 'label': label, 'icon': icon, 'required': required, 'available': key in available,
              'image': images.get(key)}
             for key, label, icon, required in SLOTS]

    saved_builds = []
    if current_user.is_authenticated:
        saved_builds = PCBuild.query.filter_by(user_id=current_user.id).order_by(PCBuild.id.desc()).all()
    public_builds = PCBuild.query.filter_by(is_public=True).order_by(PCBuild.id.desc()).limit(6).all()

    return render_template('pc_builder/builder.html',
                           title='PC Konfigurator',
                           slots=slots,
                           saved_builds=saved_builds,
                           public_builds=public_builds,
                           add_to_cart_form=AddToCartForm())


@builder_bp.route('/components/<component_type>')
def get_components(component_type):
    """AJAX endpoint to get components by type"""
    try:
        # Get components of specified type and in stock, eager load images to avoid N+1
        components = Product.query.filter_by(
            component_type=component_type
        ).filter(
            Product.stock > 0
        ).options(
            joinedload(Product.images),
            joinedload(Product.attribute_values).joinedload(ProductAttributeValue.attribute)
        ).all()

        # Filter out RAM components with Namena = "Laptop"
        if component_type == "RAM":
            filtered_components = []
            for component in components:
                # Check if this RAM has Namena attribute set to "Laptop"
                is_laptop_ram = False
                for attr_value in component.attribute_values:
                    if attr_value.attribute.name == "Namena" and attr_value.value == "Laptop":
                        is_laptop_ram = True
                        break
                if not is_laptop_ram:
                    filtered_components.append(component)
            components = filtered_components

        # Format for JSON response
        components_data = []
        for component in components:
            # Find the primary image or fallback to the first image
            primary_image = next((img for img in component.images if img.is_primary), None)
            if not primary_image and component.images:
                primary_image = component.images[0]
            image_url = (
                url_for('static', filename=primary_image.image_path)
                if primary_image else url_for('static', filename='img/no-image.svg')
            )
            components_data.append({
                'id': component.id,
                'name': component.name,
                'price': component.price,
                'image_url': image_url,
                'stock': component.stock,
                'url': url_for('product.product_detail', slug=component.slug),
                'attrs': {av.attribute.name: av.value for av in component.attribute_values if av.value},
            })
        components_data.sort(key=lambda c: c['price'])

        return jsonify({
            'success': True,
            'components': components_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@builder_bp.route('/save', methods=['POST'])
@login_required
def save_build():
    """Save a PC build configuration"""
    try:
        # Get build data from request
        build_data = request.json

        # Validate
        if not build_data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Naziv konfiguracije je obavezan'
            })

        if not build_data.get('components'):
            return jsonify({
                'success': False,
                'message': 'Nema izabranih komponenti'
            })

        # Create new build
        build = PCBuild(
            user_id=current_user.id,
            name=build_data.get('name'),
            description=build_data.get('description', ''),
            is_public=build_data.get('is_public', False)
        )

        # Add to database to get ID
        db.session.add(build)
        db.session.flush()

        # Add components
        component_ids = build_data.get('components')
        for component_id in component_ids:
            # Check if component exists
            product = Product.query.get(component_id)
            if not product:
                continue

            # Add to build
            stmt = build_components.insert().values(
                build_id=build.id,
                product_id=component_id,
                quantity=1
            )
            db.session.execute(stmt)

        # Commit changes
        db.session.commit()

        return jsonify({
            'success': True,
            'build_id': build.id,
            'message': 'Konfiguracija je uspešno sačuvana!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Greška pri čuvanju konfiguracije: {str(e)}'
        })


@builder_bp.route('/load/<int:build_id>')
def load_build(build_id):
    """Load a saved PC build configuration (AJAX endpoint)"""
    try:
        build = PCBuild.query.get_or_404(build_id)

        # Check if build is public or belongs to current user
        if not build.is_public and (not current_user.is_authenticated or build.user_id != current_user.id):
            return jsonify({
                'success': False,
                'message': 'Nemate dozvolu da učitate ovu konfiguraciju.'
            }), 403

        # Get components with their details
        components_data = []
        for component in build.components:
            # Find the primary image or fallback to the first image
            primary_image = next((img for img in component.images if img.is_primary), None)
            if not primary_image and component.images:
                primary_image = component.images[0]
            image_url = (
                url_for('static', filename=primary_image.image_path)
                if primary_image else url_for('static', filename='img/no-image.svg')
            )

            components_data.append({
                'id': component.id,
                'name': component.name,
                'price': component.price,
                'component_type': component.component_type,
                'image_url': image_url,
                'stock': component.stock,
                'url': url_for('product.product_detail', slug=component.slug),
                'attrs': {av.attribute.name: av.value for av in component.attribute_values if av.value},
            })

        return jsonify({
            'success': True,
            'build': {
                'id': build.id,
                'name': build.name,
                'description': build.description,
                'components': components_data
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Greška pri učitavanju konfiguracije: {str(e)}'
        }), 500


@builder_bp.route('/build/<int:build_id>')
def view_build(build_id):
    """View a saved PC build"""
    build = PCBuild.query.get_or_404(build_id)

    # Check if build is public or belongs to current user
    if not build.is_public and (not current_user.is_authenticated or build.user_id != current_user.id):
        flash('Nemate dozvolu da pregledate ovu konfiguraciju.', 'danger')
        return redirect(url_for('builder.builder'))

    # Get components
    components = build.components

    # Check compatibility
    is_compatible, compatibility_messages = check_pc_build_compatibility(components)

    # Calculate total price
    total_price = sum(component.price for component in components)

    # Add to cart form
    add_to_cart_form = AddToCartForm()

    return render_template('pc_builder/view_build.html',
                          title=f'PC Konfiguracija: {build.name}',
                          build=build,
                          components=components,
                          is_compatible=is_compatible,
                          compatibility_messages=compatibility_messages,
                          total_price=total_price,
                          add_to_cart_form=add_to_cart_form)


@builder_bp.route('/build/<int:build_id>/delete', methods=['POST'])
@login_required
def delete_build(build_id):
    """Delete a saved PC build"""
    build = PCBuild.query.get_or_404(build_id)

    # Check if build belongs to current user
    if build.user_id != current_user.id:
        flash('Nemate dozvolu da obrišete ovu konfiguraciju.', 'danger')
        return redirect(url_for('builder.builder'))

    # Delete build
    db.session.delete(build)
    db.session.commit()

    flash(f'Konfiguracija "{build.name}" je obrisana.', 'success')
    return redirect(url_for('builder.builder'))


@builder_bp.route('/build/<int:build_id>/add-to-cart', methods=['POST'])
@login_required
def add_build_to_cart(build_id):
    """Add all components from a build to the cart"""
    from models import CartItem
    from flask import request
    from flask_wtf.csrf import validate_csrf
    import logging

    # Get the CSRF token from the form
    csrf_token = request.form.get('csrf_token')

    # Log the CSRF token for debugging
    logging.info(f"CSRF token: {csrf_token}")

    # Skip CSRF validation for now to see if that's the issue
    if not csrf_token:
        logging.warning("No CSRF token found in form submission")
        # Continue anyway for testing

    build = PCBuild.query.get_or_404(build_id)

    # Get components
    components = build.components

    # Add each component to cart
    added_count = 0
    for component in components:
        # Check if in stock
        if component.stock <= 0:
            flash(f'{component.name} nije na stanju i nije dodat u korpu.', 'warning')
            continue

        # Check if already in cart
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=component.id
        ).first()

        if cart_item:
            # Update quantity
            cart_item.quantity += 1
        else:
            # Add new item
            cart_item = CartItem(
                user_id=current_user.id,
                product_id=component.id,
                quantity=1
            )
            db.session.add(cart_item)

        added_count += 1

    # Commit changes
    db.session.commit()

    if added_count > 0:
        flash(f'Dodato {added_count} komponenti iz konfiguracije "{build.name}" u vašu korpu!', 'success')
    else:
        flash('Nijedna komponenta nije dodata u vašu korpu.', 'warning')

    return redirect(url_for('cart.view_cart'))


@builder_bp.route('/check-compatibility', methods=['POST'])
@csrf.exempt
def check_compatibility():
    """AJAX: provjere kompatibilnosti i procjena potrošnje za izabrane komponente."""
    data = request.get_json(silent=True) or {}
    ids = [i for i in data.get('components', []) if isinstance(i, int)]
    components = Product.query.filter(Product.id.in_(ids)).options(
        joinedload(Product.attribute_values).joinedload(ProductAttributeValue.attribute)).all() if ids else []
    result = analyze_build(components)
    is_compatible, messages = check_pc_build_compatibility(components)
    return jsonify({'success': True, 'is_compatible': result['is_compatible'], 'messages': messages, **result})
