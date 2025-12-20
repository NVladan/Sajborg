# Upgrading Existing Routes with File Upload Validation

This guide shows how to add file upload validation to your existing admin routes.

---

## Routes That Need Updating

Based on the codebase analysis, these routes currently handle file uploads and should be updated:

1. **Admin Product Image Upload** - `routes/admin/product_image_routes.py`
2. **Admin Product Creation** - `routes/admin/product_routes.py`
3. **Admin Category Image Upload** - `routes/admin/category_routes.py`
4. **Blog Post Image Upload** - `routes/admin/blog_routes.py`

---

## Example: Updating Product Image Upload

### Before (Unsafe):

```python
from flask import request, flash
from werkzeug.utils import secure_filename
import os

@admin_bp.route('/product/<int:product_id>/upload-image', methods=['POST'])
def upload_product_image(product_id):
    if 'image' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(...)

    file = request.files['image']

    # PROBLEM: No validation of file type or size!
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    flash('Image uploaded successfully', 'success')
    return redirect(...)
```

### After (Secure):

```python
from flask import request, flash, current_app
from utils import validate_image_upload, secure_filename_custom
import os

@admin_bp.route('/product/<int:product_id>/upload-image', methods=['POST'])
def upload_product_image(product_id):
    if 'image' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(...)

    file = request.files['image']

    # VALIDATION: Check file type and size
    is_valid, error_message = validate_image_upload(file)
    if not is_valid:
        flash(error_message, 'error')
        return redirect(url_for('admin.edit_product', product_id=product_id))

    # SECURITY: Sanitize filename (more strict than werkzeug)
    filename = secure_filename_custom(file.filename)

    # OPTIONAL: Add unique prefix to prevent filename collisions
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"

    # Save the file
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
    os.makedirs(upload_folder, exist_ok=True)  # Ensure directory exists
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # Save to database
    # ... your existing database code ...

    flash('Image uploaded successfully', 'success')
    return redirect(...)
```

---

## Example: Updating Category Image Upload

```python
from utils import validate_image_upload, secure_filename_custom

@admin_bp.route('/category/create', methods=['POST'])
def create_category():
    # ... existing form validation ...

    # Handle image upload
    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']

        # Validate
        is_valid, error_message = validate_image_upload(file)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('admin/category_form.html', form=form)

        # Sanitize filename
        filename = secure_filename_custom(file.filename)

        # Add category slug to filename for organization
        filename = f"category_{form.slug.data}_{filename}"

        # Save
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'categories')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Store relative path in database
        category.image_path = f'uploads/categories/{filename}'

    # ... rest of your code ...
```

---

## Example: Updating Blog Post Image Upload

```python
from utils import validate_image_upload, secure_filename_custom

@admin_bp.route('/blog/post/create', methods=['POST'])
def create_blog_post():
    # ... existing form validation ...

    # Handle featured image
    if 'featured_image' in request.files:
        file = request.files['featured_image']

        if file.filename != '':
            # Validate
            is_valid, error_message = validate_image_upload(file)
            if not is_valid:
                flash(error_message, 'error')
                return render_template('admin/post_editor.html', form=form)

            # Sanitize
            filename = secure_filename_custom(file.filename)

            # Use post slug in filename
            post_slug = form.slug.data or 'post'
            filename = f"post_{post_slug}_{filename}"

            # Save
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'posts')
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))

            post.featured_image = f'uploads/posts/{filename}'

    # ... rest of your code ...
```

---

## Validation Options

### For Images:

```python
from utils import validate_image_upload

# Returns: (is_valid: bool, error_message: str or None)
is_valid, error = validate_image_upload(file)

# Allowed types: png, jpg, jpeg, gif, webp
# Max size: 5MB
```

### For Documents:

```python
from utils import validate_document_upload

# Returns: (is_valid: bool, error_message: str or None)
is_valid, error = validate_document_upload(file)

# Allowed types: pdf, doc, docx, txt
# Max size: 10MB
```

### Custom Validation:

If you need different limits, you can modify `utils.py`:

```python
# In utils.py, change these constants:
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}  # Add svg
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # Change to 10MB
```

---

## Best Practices

### 1. Always Validate Before Saving

```python
# WRONG - Save first, validate later
file.save(path)
if not is_image(path):
    os.remove(path)  # Too late!

# RIGHT - Validate first
is_valid, error = validate_image_upload(file)
if is_valid:
    file.save(path)
```

### 2. Use Unique Filenames

```python
# Prevent filename collisions
import uuid
from datetime import datetime

# Option 1: Timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"{timestamp}_{secure_filename_custom(file.filename)}"

# Option 2: UUID
unique_id = uuid.uuid4().hex[:8]
filename = f"{unique_id}_{secure_filename_custom(file.filename)}"

# Option 3: Database ID (if available)
filename = f"product_{product.id}_{secure_filename_custom(file.filename)}"
```

### 3. Organize Uploads by Type

```python
# Good structure:
static/
  uploads/
    products/
      20250113_120530_gpu.jpg
      20250113_120531_cpu.jpg
    categories/
      category_cpus_banner.jpg
    posts/
      post_new-arrival_featured.jpg
```

### 4. Handle Upload Errors Gracefully

```python
try:
    is_valid, error = validate_image_upload(file)
    if not is_valid:
        flash(error, 'error')
        return redirect(...)

    filename = secure_filename_custom(file.filename)
    file_path = os.path.join(upload_folder, filename)

    # Ensure directory exists
    os.makedirs(upload_folder, exist_ok=True)

    # Save file
    file.save(file_path)

except Exception as e:
    current_app.logger.error(f"Upload failed: {str(e)}")
    flash('Upload failed. Please try again.', 'error')
    return redirect(...)
```

### 5. Delete Old Files When Updating

```python
# When updating a product image
if product.image_path:
    old_path = os.path.join(current_app.root_path, 'static', product.image_path)
    if os.path.exists(old_path):
        try:
            os.remove(old_path)
        except Exception as e:
            current_app.logger.warning(f"Could not delete old image: {e}")

# Save new image
product.image_path = f'uploads/products/{new_filename}'
```

---

## Testing Your Changes

### Manual Testing Checklist:

- [ ] Upload valid image (jpg, png) - Should work
- [ ] Upload image larger than 5MB - Should reject with error
- [ ] Upload non-image file (txt, exe) - Should reject with error
- [ ] Upload with malicious filename (`../../etc/passwd.jpg`) - Should sanitize
- [ ] Upload with special characters (`image (1).jpg`) - Should sanitize
- [ ] Upload with very long filename - Should truncate
- [ ] Upload empty file - Should reject

### Automated Testing:

```python
# tests/test_file_uploads.py
from utils import validate_image_upload, secure_filename_custom
from werkzeug.datastructures import FileStorage
from io import BytesIO

def test_valid_image_upload():
    file = FileStorage(
        stream=BytesIO(b"fake image content"),
        filename="test.jpg",
        content_type="image/jpeg"
    )
    is_valid, error = validate_image_upload(file)
    assert is_valid is True
    assert error is None

def test_invalid_extension():
    file = FileStorage(
        stream=BytesIO(b"fake content"),
        filename="malware.exe",
        content_type="application/exe"
    )
    is_valid, error = validate_image_upload(file)
    assert is_valid is False
    assert "nije dozvoljen" in error

def test_filename_sanitization():
    dangerous = "../../etc/passwd.jpg"
    safe = secure_filename_custom(dangerous)
    assert safe == "etcpasswd.jpg"
    assert ".." not in safe
    assert "/" not in safe
```

---

## Migration Checklist

For each upload route:

1. [ ] Import validation functions:
   ```python
   from utils import validate_image_upload, secure_filename_custom
   ```

2. [ ] Add validation before saving:
   ```python
   is_valid, error = validate_image_upload(file)
   if not is_valid:
       flash(error, 'error')
       return redirect(...)
   ```

3. [ ] Replace `secure_filename` with `secure_filename_custom`:
   ```python
   filename = secure_filename_custom(file.filename)
   ```

4. [ ] Add unique prefix (optional but recommended):
   ```python
   from datetime import datetime
   timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
   filename = f"{timestamp}_{filename}"
   ```

5. [ ] Ensure upload directory exists:
   ```python
   os.makedirs(upload_folder, exist_ok=True)
   ```

6. [ ] Add try-except for error handling:
   ```python
   try:
       file.save(file_path)
   except Exception as e:
       current_app.logger.error(f"Upload failed: {e}")
       flash('Upload failed', 'error')
   ```

7. [ ] Test thoroughly (see checklist above)

---

## Quick Reference

```python
# Import
from utils import validate_image_upload, validate_document_upload, secure_filename_custom

# Validate image
is_valid, error = validate_image_upload(request.files['image'])

# Validate document
is_valid, error = validate_document_upload(request.files['document'])

# Sanitize filename
safe_name = secure_filename_custom(file.filename)

# Full example
if 'image' in request.files:
    file = request.files['image']

    is_valid, error = validate_image_upload(file)
    if not is_valid:
        flash(error, 'error')
        return redirect(...)

    filename = secure_filename_custom(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
```

---

## Need Help?

- Check `utils.py` (lines 201-326) for implementation details
- See `PHASE1_COMPLETED.md` for overview
- Run `python -c "from utils import validate_image_upload; help(validate_image_upload)"` for documentation

**Remember:** Always validate user input, especially file uploads!
