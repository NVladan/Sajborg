from flask import render_template, redirect, url_for, flash, request, current_app
from extensions import db
from models import Product, Category, ProductImage, ProductAttributeValue
from forms.product_forms import ProductForm
from . import admin_bp, admin_required
from .product_image_routes import save_product_images
import os
from slugify import slugify


@admin_bp.route('/products')
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    category_id = request.args.get('category_id', type=int)
    show_out_of_stock = request.args.get('show_out_of_stock', 'false').lower() == 'true'

    # Query for categories to create tabs
    categories = Category.query.order_by(Category.name.asc()).all()

    # Base query for products
    query = Product.query

    # Filter by category if a category tab is selected
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Filter by search query
    if search_query:
        query = query.filter(Product.name.ilike(f'%{search_query}%'))

    # Filter out of stock products unless requested
    if not show_out_of_stock:
        query = query.filter(Product.stock > 0)

    # Sortiranje prvo po kategoriji, pa po imenu proizvoda
    query = query.join(Category).order_by(Category.name.asc(), Product.name.asc())
    
    products_pagination = query.paginate(page=page, per_page=10, error_out=False)

    return render_template('admin/products.html',
                           title='Upravljanje Proizvodima',
                           products=products_pagination,
                           categories=categories,
                           search_query=search_query,
                           selected_category_id=category_id,
                           show_out_of_stock=show_out_of_stock)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    form = ProductForm()

    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]

    if form.validate_on_submit():
        category = Category.query.get(form.category_id.data)

        # Generisanje sluga
        product_slug = slugify(form.name.data)
        # Provera da li slug već postoji i dodavanje broja ako postoji
        counter = 1
        unique_slug = product_slug
        while Product.query.filter_by(slug=unique_slug).first():
            unique_slug = f"{product_slug}-{counter}"
            counter += 1

        product = Product(
            name=form.name.data,
            slug=unique_slug,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            specs=form.specs.data,
            category_id=form.category_id.data,
            component_type=category.component_type if category else None,
            featured=form.featured.data,
            condition=form.condition.data,
            availability=form.availability.data,  # Dodajemo dostupnost
            is_publicly_visible=form.stock.data > 0
        )
        db.session.add(product)
        db.session.commit()

        update_product_attributes(product, request.form)

        if 'images' in request.files:
            success_count, errors = save_product_images(product, request.files.getlist('images'))
            if errors:
                for error in errors:
                    flash(error, 'warning')
            if success_count > 0:
                flash(f'{success_count} slika(e) su uspešno uploadovane.', 'info')

        flash('Proizvod je uspešno kreiran!', 'success')
        return redirect(url_for('admin.products'))

    all_category_attributes = {}
    for category in Category.query.all():
        attributes_data = []
        for attr in category.attributes:
            attr_info = {'id': attr.id, 'name': attr.name, 'type': attr.type}
            if attr.type == 'select':
                attr_info['options'] = [opt.value for opt in attr.options]
            attributes_data.append(attr_info)
        all_category_attributes[category.id] = attributes_data

    return render_template('admin/product_form.html',
                           title='Dodaj Novi Proizvod',
                           form=form,
                           product=None,
                           all_category_attributes=all_category_attributes,
                           attribute_values={})


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]

    if form.validate_on_submit():
        category = Category.query.get(form.category_id.data)

        product.name = form.name.data

        # Ažuriranje sluga
        product_slug = slugify(form.name.data)
        # Provera da li slug već postoji i dodavanje broja ako postoji
        counter = 1
        unique_slug = product_slug
        # Proveravamo da li postoji drugi proizvod sa istim slug-om
        other_product = Product.query.filter_by(slug=unique_slug).first()
        while other_product and other_product.id != product.id:
            unique_slug = f"{product_slug}-{counter}"
            counter += 1
            other_product = Product.query.filter_by(slug=unique_slug).first()

        product.slug = unique_slug
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.specs = form.specs.data
        product.category_id = form.category_id.data
        product.component_type = category.component_type if category else None
        product.featured = form.featured.data
        product.condition = form.condition.data
        product.availability = form.availability.data  # Ažuriramo dostupnost
        product.is_publicly_visible = form.stock.data > 0

        db.session.commit()
        update_product_attributes(product, request.form)

        if 'images' in request.files:
            success_count, errors = save_product_images(product, request.files.getlist('images'))
            if errors:
                for error in errors:
                    flash(error, 'warning')
            if success_count > 0:
                flash(f'{success_count} slika(e) su uspešno uploadovane.', 'info')

        flash('Proizvod je uspešno ažuriran!', 'success')
        return redirect(url_for('admin.products'))

    if request.method == 'GET':
        form.category_id.data = product.category_id
        form.condition.data = product.condition
        form.availability.data = product.availability  # Popunjavamo polje prilikom GET zahtjeva

    all_category_attributes = {}
    for category in Category.query.all():
        attributes_data = []
        for attr in category.attributes:
            attr_info = {'id': attr.id, 'name': attr.name, 'type': attr.type}
            if attr.type == 'select':
                attr_info['options'] = [opt.value for opt in attr.options]
            attributes_data.append(attr_info)
        all_category_attributes[category.id] = attributes_data

    attribute_values = {val.attribute_id: val.value for val in product.attribute_values}
    images_sorted = sorted(product.images, key=lambda x: x.sort_order)

    return render_template('admin/product_form.html',
                           title='Izmeni Proizvod',
                           form=form,
                           product=product,
                           all_category_attributes=all_category_attributes,
                           attribute_values=attribute_values,
                           images_sorted=images_sorted,
                           is_edit=True)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Delete associated image files
    for image in product.images:
        try:
            os.remove(os.path.join(current_app.static_folder, image.image_path))
        except (FileNotFoundError, PermissionError) as e:
            flash(f"Could not delete image {image.image_path}: {e}", "warning")

    db.session.delete(product)
    db.session.commit()
    flash('Proizvod je uspešno obrisan.', 'success')
    return redirect(url_for('admin.products'))


def update_product_attributes(product, form_data):
    category_attributes = product.category.attributes
    existing_attribute_values = {pav.attribute_id: pav for pav in product.attribute_values}

    attributes_to_add = []
    attributes_to_delete = []

    for attr in category_attributes:
        form_field_name = f'attribute_{attr.id}'
        attribute_value_str = form_data.get(form_field_name)

        if attribute_value_str is not None and attribute_value_str.strip() != '':
            try:
                if attr.type == 'int':
                    value = int(attribute_value_str)
                elif attr.type == 'float':
                    value = float(attribute_value_str)
                elif attr.type == 'bool':
                    value = attribute_value_str.lower() in ('true', '1', 'yes')
                else:
                    value = attribute_value_str
            except ValueError:
                flash(f"Nevažeća vrednost za atribut '{attr.name}'. Pokušajte ponovo.", 'warning')
                continue

            if attr.id in existing_attribute_values:
                existing_attribute_values[attr.id].value = str(value)
            else:
                attributes_to_add.append(
                    ProductAttributeValue(product_id=product.id, attribute_id=attr.id, value=str(value)))
        elif attr.id in existing_attribute_values:
            attributes_to_delete.append(existing_attribute_values[attr.id])

    if attributes_to_add:
        db.session.bulk_save_objects(attributes_to_add)
    if attributes_to_delete:
        for pav in attributes_to_delete:
            db.session.delete(pav)

    db.session.commit()