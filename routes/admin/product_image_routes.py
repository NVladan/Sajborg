import os
import secrets
from flask import redirect, url_for, flash, request, current_app, jsonify
from extensions import db
from models import ProductImage
from utils import validate_image_upload, secure_filename_custom
from . import admin_bp, admin_required

def save_product_images(product, files):
    """
    Helper function to save product images with validation.

    Args:
        product: Product model instance
        files: List of FileStorage objects

    Returns:
        tuple: (success_count: int, error_messages: list)
    """
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products', str(product.id))
    os.makedirs(upload_folder, exist_ok=True)

    success_count = 0
    errors = []

    for file in files:
        if file and file.filename != '':
            # Validate the image file
            is_valid, error_message = validate_image_upload(file)
            if not is_valid:
                errors.append(f"{file.filename}: {error_message}")
                continue

            # Generate secure filename
            random_hex = secrets.token_hex(8)
            safe_filename = secure_filename_custom(file.filename)
            _, f_ext = os.path.splitext(safe_filename)
            picture_fn = random_hex + f_ext

            picture_path_local = os.path.join(upload_folder, picture_fn)

            try:
                file.save(picture_path_local)
                picture_path_for_db = f"uploads/products/{product.id}/{picture_fn}"

                image = ProductImage(product_id=product.id, image_path=picture_path_for_db)

                # Set as primary if no primary image exists
                if not any(img.is_primary for img in product.images):
                    image.is_primary = True

                db.session.add(image)
                success_count += 1

            except Exception as e:
                current_app.logger.error(f"Failed to save image {file.filename}: {str(e)}")
                errors.append(f"{file.filename}: Greška pri čuvanju fajla")

    if success_count > 0:
        db.session.commit()

    return success_count, errors


@admin_bp.route('/products/delete-image/<int:image_id>', methods=['POST'])
@admin_required
def delete_product_image(image_id):
    image = ProductImage.query.get_or_404(image_id)
    product_id = image.product_id

    if len(image.product.images) == 1:
        flash('Ne možete obrisati jedinu sliku proizvoda. Dodajte novu primarnu sliku pre brisanja.', 'danger')
        return redirect(url_for('admin.edit_product', product_id=product_id))

    if image.is_primary:
        next_primary_image = ProductImage.query.filter(
            ProductImage.product_id == product_id,
            ProductImage.id != image_id
        ).first()
        if next_primary_image:
            next_primary_image.is_primary = True
            db.session.add(next_primary_image)
        else:
            flash('Greška: Nije pronađena zamenska primarna slika.', 'warning')

    try:
        static_path = os.path.join(current_app.static_folder)
        full_path = os.path.join(static_path, image.image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        flash(f'Error deleting file: {e}', 'danger')

    db.session.delete(image)
    db.session.commit()

    flash('Product image deleted successfully.', 'success')
    return redirect(url_for('admin.edit_product', product_id=product_id))


@admin_bp.route('/products/set-primary-image/<int:image_id>', methods=['POST'])
@admin_required
def set_primary_image(image_id):
    image = ProductImage.query.get_or_404(image_id)
    product = image.product

    for img in product.images:
        img.is_primary = False

    image.is_primary = True
    db.session.commit()

    flash('Glavna slika je uspešno ažurirana.', 'success')
    return redirect(url_for('admin.edit_product', product_id=product.id))


@admin_bp.route('/products/update-image-order', methods=['POST'])
@admin_required
def update_image_order():
    image_order = request.json.get('order')
    product_id = -1
    if image_order:
        for index, image_id in enumerate(image_order):
            image = ProductImage.query.get(int(image_id))
            if image:
                image.sort_order = index
                product_id = image.product_id
        db.session.commit()
        flash('Redosled slika je ažuriran.', 'success')

    if product_id != -1:
        return jsonify({'success': True, 'redirect_url': url_for('admin.edit_product', product_id=product_id)})
    return jsonify({'success': False})