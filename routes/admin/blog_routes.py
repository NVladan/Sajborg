import os
import secrets
from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user
from extensions import db
from models import Post
from forms.product_forms import PostForm
from utils import validate_image_upload, secure_filename_custom
from . import admin_bp, admin_required


@admin_bp.route('/posts')
@admin_required
def posts():
    """Prikazuje sve blog postove u admin panelu."""
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', title='Upravljanje Člancima', posts=posts)


@admin_bp.route('/posts/add', methods=['GET', 'POST'])
@admin_required
def add_post():
    """Prikazuje formu i obrađuje dodavanje novog blog posta."""
    form = PostForm()
    if form.validate_on_submit():
        slug = form.title.data.lower().replace(' ', '-').replace('č', 'c').replace('ć', 'c').replace('š', 's').replace('đ', 'dj').replace('ž', 'z')
        slug = ''.join(e for e in slug if e.isalnum() or e == '-')

        post = Post(
            title=form.title.data,
            slug=slug,
            content=form.content.data,
            author_id=current_user.id,
            is_published=form.is_published.data
        )

        if form.featured_image.data:
            file = form.featured_image.data

            # Validate the image
            is_valid, error_message = validate_image_upload(file)
            if not is_valid:
                flash(f'Greška pri upload-u slike: {error_message}', 'error')
                return render_template('admin/post_form.html', title='Dodaj Novi Članak', form=form, is_edit=False)

            # Generate secure filename
            safe_filename = secure_filename_custom(file.filename)
            filename = secrets.token_hex(8) + os.path.splitext(safe_filename)[1]

            # Save the file
            upload_folder = os.path.join(current_app.static_folder, 'uploads/posts')
            os.makedirs(upload_folder, exist_ok=True)
            image_save_path = os.path.join(upload_folder, filename)

            try:
                file.save(image_save_path)
                post.featured_image = f"uploads/posts/{filename}"
            except Exception as e:
                current_app.logger.error(f"Failed to save featured image: {str(e)}")
                flash('Greška pri čuvanju slike. Pokušajte ponovo.', 'error')
                return render_template('admin/post_form.html', title='Dodaj Novi Članak', form=form, is_edit=False)

        db.session.add(post)
        db.session.commit()
        flash('Članak je uspešno kreiran!', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/post_form.html', title='Dodaj Novi Članak', form=form, is_edit=False)


@admin_bp.route('/posts/edit/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def edit_post(post_id):
    """Prikazuje formu i obrađuje izmenu postojećeg blog posta."""
    post = Post.query.get_or_404(post_id)
    form = PostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.title.data.lower().replace(' ', '-').replace('č', 'c').replace('ć', 'c').replace('š', 's').replace('đ', 'dj').replace('ž', 'z')
        post.slug = ''.join(e for e in post.slug if e.isalnum() or e == '-')
        post.content = form.content.data
        post.is_published = form.is_published.data

        if form.featured_image.data:
            file = form.featured_image.data

            # Validate the image
            is_valid, error_message = validate_image_upload(file)
            if not is_valid:
                flash(f'Greška pri upload-u slike: {error_message}', 'error')
                return render_template('admin/post_form.html', title='Izmeni Članak', form=form, post=post, is_edit=True)

            # Delete old image if exists
            if post.featured_image:
                try:
                    old_image_path = os.path.join(current_app.static_folder, post.featured_image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except (FileNotFoundError, PermissionError) as e:
                    current_app.logger.warning(f"Could not delete old image: {e}")

            # Generate secure filename
            safe_filename = secure_filename_custom(file.filename)
            filename = secrets.token_hex(8) + os.path.splitext(safe_filename)[1]

            # Save the file
            upload_folder = os.path.join(current_app.static_folder, 'uploads/posts')
            os.makedirs(upload_folder, exist_ok=True)
            image_save_path = os.path.join(upload_folder, filename)

            try:
                file.save(image_save_path)
                post.featured_image = f"uploads/posts/{filename}"
            except Exception as e:
                current_app.logger.error(f"Failed to save featured image: {str(e)}")
                flash('Greška pri čuvanju slike. Pokušajte ponovo.', 'error')
                return render_template('admin/post_form.html', title='Izmeni Članak', form=form, post=post, is_edit=True)

        db.session.commit()
        flash('Članak je uspešno ažuriran!', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/post_form.html', title='Izmeni Članak', form=form, post=post, is_edit=True)


@admin_bp.route('/posts/delete/<int:post_id>', methods=['POST'])
@admin_required
def delete_post(post_id):
    """Briše blog post."""
    post = Post.query.get_or_404(post_id)
    if post.featured_image:
        try:
            os.remove(os.path.join(current_app.static_folder, post.featured_image))
        except (FileNotFoundError, PermissionError) as e:
            flash(f"Could not delete image for post {post.title}: {e}", "warning")

    db.session.delete(post)
    db.session.commit()
    flash('Članak je uspešno obrisan.', 'success')
    return redirect(url_for('admin.posts'))


@admin_bp.route('/posts/upload_image', methods=['POST'])
@admin_required
def upload_post_image():
    """Funkcija za upload slike unutar Summernote editora."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})

    # Validate the image
    is_valid, error_message = validate_image_upload(file)
    if not is_valid:
        return jsonify({'success': False, 'error': error_message})

    try:
        # Generate secure filename
        safe_filename = secure_filename_custom(file.filename)
        filename = secrets.token_hex(8) + os.path.splitext(safe_filename)[1]

        # Save file
        upload_folder = os.path.join(current_app.static_folder, 'uploads/posts')
        os.makedirs(upload_folder, exist_ok=True)
        image_save_path = os.path.join(upload_folder, filename)
        file.save(image_save_path)

        # Return URL
        image_url = url_for('static', filename=f'uploads/posts/{filename}')
        return jsonify({'success': True, 'url': image_url})

    except Exception as e:
        current_app.logger.error(f"Failed to upload Summernote image: {str(e)}")
        return jsonify({'success': False, 'error': 'File upload failed'})