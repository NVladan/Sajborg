import os
import secrets
from flask import render_template, redirect, url_for, flash, request, current_app
from extensions import db
from models import Category, CategoryAttribute, AttributeOption
from forms.product_forms import CategoryForm
from utils import validate_image_upload, secure_filename_custom
from . import admin_bp, admin_required


@admin_bp.route('/categories')
@admin_required
def categories():
    categories = Category.query.filter_by(parent_id=None).order_by('name').all()
    return render_template('admin/categories.html',
                           title='Upravljanje Kategorijama',
                           categories=categories)


@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    form = CategoryForm()
    form.parent_id.choices = [(0, 'None')] + [(c.id, c.name) for c in Category.query.order_by('name').all()]

    # Popunjavanje choices za novo polje component_type
    component_types = current_app.config.get('COMPONENT_TYPES', [])
    form.component_type.choices = [('', 'N/A')] + [(ct, ct) for ct in component_types]

    if form.validate_on_submit():
        parent_id = form.parent_id.data if form.parent_id.data and form.parent_id.data > 0 else None

        # Provera da li slug već postoji, ako ne, generiši ga
        slug = form.slug.data
        if not slug:
            slug = form.name.data.lower().replace(' ', '-').replace('č', 'c').replace('ć', 'c').replace('š',
                                                                                                        's').replace(
                'đ', 'dj').replace('ž', 'z')
            slug = ''.join(e for e in slug if e.isalnum() or e == '-')

        category = Category(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            parent_id=parent_id,
            is_featured=form.is_featured.data,
            component_type=form.component_type.data  # Čuvanje novog polja
        )
        if form.image.data:
            file = form.image.data

            # Validate the image
            is_valid, error_message = validate_image_upload(file)
            if not is_valid:
                flash(f'Greška pri upload-u slike: {error_message}', 'error')
                return render_template('admin/category_form.html', title='Dodaj Novu Kategoriju', form=form, is_edit=False)

            # Generate secure filename
            safe_filename = secure_filename_custom(file.filename)
            filename = secrets.token_hex(8) + os.path.splitext(safe_filename)[1]

            # Save file
            upload_folder = os.path.join(current_app.static_folder, 'uploads/categories')
            os.makedirs(upload_folder, exist_ok=True)
            image_save_path = os.path.join(upload_folder, filename)

            try:
                file.save(image_save_path)
                category.image_path = f"uploads/categories/{filename}"
            except Exception as e:
                current_app.logger.error(f"Failed to save category image: {str(e)}")
                flash('Greška pri čuvanju slike. Pokušajte ponovo.', 'error')
                return render_template('admin/category_form.html', title='Dodaj Novu Kategoriju', form=form, is_edit=False)
        db.session.add(category)
        db.session.commit()
        flash('Kategorija je uspešno kreirana!', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/category_form.html',
                           title='Dodaj Novu Kategoriju',
                           form=form,
                           is_edit=False)


@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    form.parent_id.choices = [(0, 'None')] + [(c.id, c.name) for c in
                                              Category.query.filter(Category.id != category_id).order_by('name').all()]

    # Popunjavanje choices za novo polje component_type
    component_types = current_app.config.get('COMPONENT_TYPES', [])
    form.component_type.choices = [('', 'N/A')] + [(ct, ct) for ct in component_types]

    if form.validate_on_submit():
        category.name = form.name.data
        category.slug = form.slug.data
        category.description = form.description.data
        category.parent_id = form.parent_id.data if form.parent_id.data and form.parent_id.data > 0 else None
        category.is_featured = form.is_featured.data
        category.component_type = form.component_type.data  # Čuvanje novog polja

        if form.image.data:
            file = form.image.data

            # Validate the image
            is_valid, error_message = validate_image_upload(file)
            if not is_valid:
                flash(f'Greška pri upload-u slike: {error_message}', 'error')
                return render_template('admin/category_form.html', title='Izmeni Kategoriju', form=form, category=category, is_edit=True)

            # Delete old image if exists and is not default
            if category.image_path and category.image_path != 'img/category-default.png':
                try:
                    old_image_path = os.path.join(current_app.static_folder, category.image_path)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except (FileNotFoundError, PermissionError) as e:
                    current_app.logger.warning(f"Could not delete old image: {e}")

            # Generate secure filename
            safe_filename = secure_filename_custom(file.filename)
            filename = secrets.token_hex(8) + os.path.splitext(safe_filename)[1]

            # Save file
            upload_folder = os.path.join(current_app.static_folder, 'uploads/categories')
            os.makedirs(upload_folder, exist_ok=True)
            image_save_path = os.path.join(upload_folder, filename)

            try:
                file.save(image_save_path)
                category.image_path = f"uploads/categories/{filename}"
            except Exception as e:
                current_app.logger.error(f"Failed to save category image: {str(e)}")
                flash('Greška pri čuvanju slike. Pokušajte ponovo.', 'error')
                return render_template('admin/category_form.html', title='Izmeni Kategoriju', form=form, category=category, is_edit=True)
        db.session.commit()
        flash('Kategorija je uspešno ažurirana!', 'success')
        return redirect(url_for('admin.categories'))

    # Pre-popunjavanje polja prilikom GET zahteva
    if request.method == 'GET':
        form.component_type.data = category.component_type

    return render_template('admin/category_form.html',
                           title='Izmeni Kategoriju',
                           form=form,
                           category=category,
                           is_edit=True)


@admin_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.products:
        flash('Nije moguće obrisati kategoriju koja sadrži proizvode.', 'danger')
        return redirect(url_for('admin.categories'))
    if category.image_path and category.image_path != 'img/category-default.png':
        try:
            os.remove(os.path.join(current_app.static_folder, category.image_path))
        except (FileNotFoundError, PermissionError) as e:
            flash(f"Could not delete image for category {category.name}: {e}", "warning")

    db.session.delete(category)
    db.session.commit()
    flash('Kategorija je uspešno obrisana.', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/toggle-featured/<int:category_id>', methods=['POST'])
@admin_required
def toggle_featured_category(category_id):
    category = Category.query.get_or_404(category_id)
    category.is_featured = not category.is_featured
    db.session.commit()
    flash(f'Featured status for category "{category.name}" has been updated.', 'success')
    return redirect(url_for('admin.categories'))


# Category Attributes Management
@admin_bp.route('/categories/<int:category_id>/attributes', methods=['GET', 'POST'])
@admin_required
def manage_attributes(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        # Add a new attribute
        attribute_name = request.form.get('name')
        attribute_type = request.form.get('type', 'string')
        if attribute_name:
            attribute = CategoryAttribute(
                name=attribute_name,
                type=attribute_type,
                category_id=category.id
            )
            db.session.add(attribute)
            db.session.commit()
            flash('Atribut je uspešno dodat.', 'success')
            return redirect(url_for('admin.manage_attributes', category_id=category_id))

    attributes = category.attributes
    return render_template('admin/category_attributes.html',
                           title=f'Upravljanje Atributima za {category.name}',
                           category=category,
                           attributes=attributes)


@admin_bp.route('/attributes/update/<int:attribute_id>', methods=['POST'])
@admin_required
def update_attribute(attribute_id):
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    attribute.name = request.form.get('name', attribute.name)
    attribute.type = request.form.get('type', attribute.type)
    db.session.commit()
    flash('Atribut je uspešno ažuriran.', 'success')
    return redirect(url_for('admin.manage_attributes', category_id=attribute.category_id))


@admin_bp.route('/attributes/delete/<int:attribute_id>', methods=['POST'])
@admin_required
def delete_attribute(attribute_id):
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    category_id = attribute.category_id
    db.session.delete(attribute)
    db.session.commit()
    flash('Atribut je uspešno obrisan.', 'success')
    return redirect(url_for('admin.manage_attributes', category_id=category_id))


@admin_bp.route('/attributes/move-up/<int:attribute_id>', methods=['POST'])
@admin_required
def move_category_attribute_up(attribute_id):
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    if attribute.sort_order > 0:
        prev_attribute = CategoryAttribute.query.filter_by(
            category_id=attribute.category_id,
            sort_order=attribute.sort_order - 1
        ).first()
        if prev_attribute:
            prev_attribute.sort_order += 1
        attribute.sort_order -= 1
        db.session.commit()
    return redirect(url_for('admin.manage_attributes', category_id=attribute.category_id))


@admin_bp.route('/attributes/move-down/<int:attribute_id>', methods=['POST'])
@admin_required
def move_category_attribute_down(attribute_id):
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    max_sort_order = db.session.query(db.func.max(CategoryAttribute.sort_order)).filter_by(
        category_id=attribute.category_id
    ).scalar()
    if attribute.sort_order < max_sort_order:
        next_attribute = CategoryAttribute.query.filter_by(
            category_id=attribute.category_id,
            sort_order=attribute.sort_order + 1
        ).first()
        if next_attribute:
            next_attribute.sort_order -= 1
        attribute.sort_order += 1
        db.session.commit()
    return redirect(url_for('admin.manage_attributes', category_id=attribute.category_id))


@admin_bp.route('/attributes/<int:attribute_id>/options', methods=['GET', 'POST'])
@admin_required
def manage_attribute_options(attribute_id):
    attribute = CategoryAttribute.query.get_or_404(attribute_id)
    if attribute.type != 'select':
        flash('Ovaj atribut nije tipa "select".', 'warning')
        return redirect(url_for('admin.manage_attributes', category_id=attribute.category_id))

    if request.method == 'POST':
        option_value = request.form.get('value')
        if option_value:
            new_option = AttributeOption(attribute_id=attribute.id, value=option_value)
            db.session.add(new_option)
            db.session.commit()
            flash(f'Opcija "{option_value}" je dodata.', 'success')
            return redirect(url_for('admin.manage_attribute_options', attribute_id=attribute_id))

    return render_template('admin/attribute_options.html', attribute=attribute)


@admin_bp.route('/attributes/options/delete/<int:option_id>', methods=['POST'])
@admin_required
def delete_attribute_option(option_id):
    option = AttributeOption.query.get_or_404(option_id)
    attribute_id = option.attribute_id
    db.session.delete(option)
    db.session.commit()
    flash(f'Opcija "{option.value}" je obrisana.', 'success')
    return redirect(url_for('admin.manage_attribute_options', attribute_id=attribute_id))