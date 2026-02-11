from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from extensions import db, csrf
from models import Product, PCBuild, build_components, ProductAttributeValue
from forms.builder_forms import PCBuildForm, AddToCartForm
from utils import check_pc_build_compatibility

builder_bp = Blueprint('builder', __name__, url_prefix='/pc-builder')

@builder_bp.route('/')
def builder():
    # Get all component types from database
    component_types = db.session.query(Product.component_type).filter(Product.component_type.isnot(None)).distinct().all()
    component_types = [c[0] for c in component_types if c[0]]

    # Create form for adding to cart
    add_to_cart_form = AddToCartForm()

    # Get saved builds if user is logged in
    saved_builds = []
    if current_user.is_authenticated:
        saved_builds = PCBuild.query.filter_by(user_id=current_user.id).all()

    # Get public builds
    public_builds = PCBuild.query.filter_by(is_public=True).limit(5).all()

    return render_template('pc_builder/builder.html',
                          title='PC Konfigurator',
                          component_types=component_types,
                          saved_builds=saved_builds,
                          public_builds=public_builds,
                          add_to_cart_form=add_to_cart_form)


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
                'specs': component.specs,
                'image_url': image_url,
                'stock': component.stock
            })

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
                'stock': component.stock
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
    """AJAX endpoint to check component compatibility"""
    try:
        print("[DEBUG] /check-compatibility called")
        print(f"[DEBUG] request.json: {request.json}")
        # Get component IDs from request
        if not request.json:
            print("[DEBUG] No JSON data received")
            return jsonify({
                'success': False,
                'message': 'Nevažeći JSON podaci',
                'is_compatible': False,
                'messages': ['Greška pri proveri kompatibilnosti: Nema podataka']
            }), 400
        component_ids = request.json.get('components', [])
        print(f"[DEBUG] component_ids: {component_ids}")
        if not component_ids:
            print("[DEBUG] No component IDs provided")
            return jsonify({
                'success': True,
                'is_compatible': True,
                'messages': ['Još uvek nema izabranih komponenti']
            })
        # Get components
        components = Product.query.filter(Product.id.in_(component_ids)).all()
        print(f"[DEBUG] Found {len(components)} components in DB for IDs: {component_ids}")
        # Check if we found all components
        if len(components) != len(component_ids):
            print("[DEBUG] Some components not found in DB")
            return jsonify({
                'success': True,
                'is_compatible': False,
                'messages': ['Neke komponente nisu pronađene u bazi podataka']
            })
        # Check compatibility
        is_compatible, messages = check_pc_build_compatibility(components)
        print(f"[DEBUG] Compatibility result: {is_compatible}, messages: {messages}")
        return jsonify({
            'success': True,
            'is_compatible': is_compatible,
            'messages': messages
        })
    except Exception as e:
        import traceback
        print(f"Error in check_compatibility route: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': str(e),
            'is_compatible': False,
            'messages': [f'Greška pri proveri kompatibilnosti: {str(e)}']
        }), 500