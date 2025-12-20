# Sajborg.com - Codebase Documentation & Improvement Guide

## Executive Summary

**Sajborg.com** is a production-ready e-commerce platform for PC components and electronics in Bosnia and Herzegovina. The application is built with Flask, follows best practices with blueprint-based architecture, and includes comprehensive features like inventory management, PC builder, payment processing, and customer support chat.

**Overall Code Quality**: 7.5/10 - Good foundation with room for improvements
**Tech Debt Level**: Moderate
**Test Coverage**: 0% (No tests exist)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Design Patterns](#architecture--design-patterns)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [Code Quality Analysis](#code-quality-analysis)
6. [Identified Issues](#identified-issues)
7. [Improvement Recommendations](#improvement-recommendations)
8. [Security Considerations](#security-considerations)
9. [Performance Optimization Opportunities](#performance-optimization-opportunities)
10. [Maintenance & Best Practices](#maintenance--best-practices)

---

## Project Overview

### Application Type
Full-featured e-commerce web application for PC parts and electronics

### Key Features
- Product catalog with advanced filtering (dynamic attributes system)
- Shopping cart with extended warranty option
- User authentication with multiple roles (admin, dobavljac, distributer, musterija)
- Admin panel for complete content management
- PC Builder/Configurator with compatibility checking
- Payment processing (Stripe + Cash on Delivery)
- Blog functionality
- Internal inventory management (Lager system)
- Real-time chat between users and admins
- Product reviews (tied to verified purchases)
- SEO optimization (sitemap, slugs, meta tags)

### Languages & Frameworks
- Backend: Python 3.x with Flask 3.0.3
- Frontend: Jinja2 templates, vanilla JavaScript, CSS
- Database: SQLite (suitable for migration to PostgreSQL)
- UI Framework: Bootstrap 3.3.7.1 with custom gradient theme

---

## Architecture & Design Patterns

### Application Structure

```
Factory Pattern (Application Creation)
├── app.py - Application factory
├── main.py - Entry point
└── config.py - Environment-based configuration

Blueprint Pattern (Modular Routes)
├── routes/auth.py - Authentication
├── routes/main.py - Homepage/static pages
├── routes/product.py - Product catalog
├── routes/cart.py - Shopping cart
├── routes/pc_builder.py - PC configurator
├── routes/lager.py - Internal inventory
├── routes/chat.py - Real-time messaging
├── routes/blog_routes.py - Blog
├── routes/seo_routes.py - SEO features
└── routes/admin/ - Admin panel (8 modules)

MVC-like Structure
├── Models: models.py (17 database models)
├── Views: templates/ (36 HTML files)
└── Controllers: routes/ (19 route modules)

Service Layer
└── utils.py - Business logic utilities
```

### Design Patterns Used

1. **Factory Pattern** - `create_app()` for application initialization
2. **Repository Pattern** - SQLAlchemy ORM models
3. **Decorator Pattern** - `@login_required`, `@admin_required`, custom role decorators
4. **Blueprint Pattern** - Modular route organization
5. **Template Method** - Base templates with inheritance

### Key Architectural Decisions

**Strengths:**
- Clear separation of concerns
- Modular blueprint-based organization
- Centralized configuration management
- Proper extension initialization
- Database migrations support (Alembic)

**Weaknesses:**
- No service layer abstraction (business logic mixed in routes)
- Limited error handling consistency
- No API layer (REST/GraphQL)
- Tight coupling between routes and database models

---

## Technology Stack

### Backend Dependencies (requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.3 | Web framework |
| SQLAlchemy | 2.0.31 | ORM |
| Flask-Login | 0.6.3 | User session management |
| Flask-Bcrypt | 1.0.1 | Password hashing |
| Flask-WTF | 1.2.1 | Form handling & CSRF protection |
| Flask-Migrate | 4.0.7 | Database migrations |
| Stripe | 10.2.0 | Payment processing |
| python-slugify | Latest | URL-friendly slugs |
| Flask-Bootstrap | 3.3.7.1 | UI framework integration |

### Development Dependencies
- pytest 8.3.5+ (configured but no tests written)
- pytest-cov 5.0.0+ (code coverage)

### Frontend Stack
- Vanilla JavaScript (9 files)
- Custom CSS (10 files) with blue-green gradient theme
- Bootstrap 3.3.7.1
- Mobile-first responsive design
- AJAX for dynamic interactions

---

## Database Schema

### Models Overview (17 total)

#### Core E-commerce Models

**User** (models.py:22-54)
```python
- Authentication: username, email, password_hash
- Profile: first_name, last_name, address, city, postal_code, country, phone_number
- Role system: role (admin/dobavljac/distributer/musterija)
- Features: is_subscribed, is_banned
- Relationships: orders, cart_items, pc_builds, reviews, messages
```

**Product** (models.py:88-124)
```python
- Basic: name, description, price, stock
- Metadata: slug, category_id, component_type
- Business: purchase_price, condition (Novo/Polovni), availability
- Visibility: is_publicly_visible, featured
- Dynamic attributes: attribute_values (EAV pattern)
- Media: images (ProductImage relationship)
```

**Category** (models.py:57-73)
```python
- Hierarchical: parent_id (self-referential)
- SEO: slug, description
- Display: image_path, is_featured
- Visibility: is_public
- Attributes: Dynamic attribute system
```

**Order** (models.py:138-161)
```python
- Core: total_amount, status, payment_method
- Shipping: All address fields separated
- Products: Many-to-many via order_items table
- Calculated: full_shipping_address property
```

#### Supporting Models

**CartItem** - Shopping cart with extended warranty option
**PCBuild** - Saved PC configurations (public/private)
**Review** - Product reviews (verified purchases only)
**Message** - Customer support chat
**Post** - Blog posts
**LagerProduct** - Internal inventory items
**LagerCategory** - Inventory categories
**Subscription** - Newsletter subscriptions

#### Dynamic Attribute System (EAV Pattern)

**CategoryAttribute** - Defines attributes for categories
**AttributeOption** - Predefined attribute values
**ProductAttributeValue** - Product-specific attribute values

### Database Relationships

```
User (1) ──< (M) Order ── order_items (association) ─< Product
User (1) ──< (M) CartItem >── (1) Product
User (1) ──< (M) PCBuild ── build_components (association) ─< Product
User (1) ──< (M) Review >── (1) Product
User (1) ──< (M) Message >── (1) User (recipient)
Category (1) ──< (M) Product
Category (1) ──< (M) Category (hierarchical)
Product (1) ──< (M) ProductImage
Product (1) ──< (M) ProductAttributeValue >── (1) CategoryAttribute
```

### Migration History
- 6 migrations in `migrations/versions/`
- Alembic properly configured
- Recent migration: Added LagerCategory.sort_order with server_default

---

## Code Quality Analysis

### Strengths

1. **Architecture**
   - Clean blueprint-based organization
   - Proper separation of routes, models, and forms
   - Application factory pattern enables testing
   - Configuration management (dev/test/prod)

2. **Security**
   - CSRF protection enabled globally
   - Password hashing with bcrypt
   - SQL injection prevention via ORM
   - Role-based access control
   - User ban functionality
   - Session security configured

3. **Database Design**
   - Proper relationships and cascades
   - Timestamps on key models
   - Soft deletes (is_publicly_visible)
   - Dynamic attribute system (flexible)
   - Migration support

4. **User Experience**
   - PC compatibility checking (utils.py:107-197)
   - Dynamic cart updates (AJAX)
   - Product filtering with attributes
   - Mobile-first responsive design
   - Verified purchase reviews

5. **Business Logic**
   - EUR to BAM conversion utility
   - Extended warranty calculation
   - PC builder compatibility checks
   - Order total calculation
   - Multi-role access (Lager system)

### Weaknesses

1. **Testing**
   - **CRITICAL**: Zero test coverage
   - pytest configured but no tests written
   - No unit, integration, or E2E tests
   - Manual testing only

2. **Code Organization**
   - Business logic mixed in route handlers
   - No service layer abstraction
   - Direct database access in routes
   - Inconsistent error handling patterns

3. **Documentation**
   - Limited inline comments
   - No docstrings on functions
   - No API documentation
   - Comments in Serbian/Croatian mixed with English code

4. **Error Handling**
   - Inconsistent exception handling
   - Generic try-except blocks (cart.py:69)
   - No centralized error logging
   - Limited user-friendly error messages

5. **Performance**
   - No query optimization
   - N+1 query problems likely exist
   - No caching layer
   - No database connection pooling
   - Recursive category queries (product.py:38-45)

6. **Dependencies**
   - Flask-Bootstrap 3.3.7.1 is outdated
   - Bootstrap 3 is deprecated (EOL)
   - No dependency version pinning for some packages
   - Missing pandas/openpyxl in requirements.txt (used in utils.py)

7. **Frontend**
   - No build system (Webpack/Vite)
   - No CSS preprocessing (SASS/LESS)
   - No JavaScript bundling/minification
   - No TypeScript
   - jQuery dependency via Bootstrap

---

## Identified Issues

### Critical Issues (Fix Immediately)

1. **No Test Coverage**
   - Location: Entire codebase
   - Impact: High risk of regressions
   - Effort: High (100+ hours to add comprehensive tests)

2. **Missing Dependencies**
   - Location: utils.py:2 (imports pandas)
   - Issue: pandas not in requirements.txt
   - Impact: Application crash on fresh install
   - Fix: Add `pandas` to requirements.txt

3. **Inconsistent Import Patterns**
   - Location: product.py:2
   - Issue: `from app import db` instead of `from extensions import db`
   - Impact: Circular import risk
   - Fix: Use `from extensions import db` consistently

4. **Hardcoded Database Path**
   - Location: app.py:43
   - Issue: Fallback to `sqlite:///pcshop.db` without instance/ prefix
   - Impact: Database created in wrong location
   - Fix: Use `sqlite:///instance/pcshop.db`

5. **No Input Validation for File Uploads**
   - Location: Product image upload, blog post images
   - Issue: No file type/size validation
   - Impact: Security risk (malicious uploads)
   - Fix: Add file validation middleware

### High Priority Issues

6. **SQL Injection Risk in Raw Queries**
   - Location: cart.py:142-148 (order_items.insert())
   - Issue: Using raw insert statements
   - Impact: Potential SQL injection (mitigated by ORM but inconsistent)
   - Fix: Use ORM relationships consistently

7. **No Rate Limiting**
   - Location: All routes
   - Issue: No protection against brute force/DoS
   - Impact: Account takeover, service disruption
   - Fix: Add Flask-Limiter

8. **Weak Session Configuration**
   - Location: app.py:23
   - Issue: Fallback to 'dev-secret-key'
   - Impact: Session hijacking in production if .env missing
   - Fix: Require SECRET_KEY in production

9. **No Email Verification**
   - Location: routes/auth.py (registration)
   - Issue: Users can register with any email
   - Impact: Fake accounts, spam
   - Fix: Add email verification flow

10. **No Pagination Limit**
    - Location: product.py:82
    - Issue: Hardcoded per_page=12
    - Impact: Cannot adjust for performance
    - Fix: Make configurable in config.py

### Medium Priority Issues

11. **Inconsistent Flash Message Categories**
    - Location: Multiple routes
    - Issue: Mix of 'success', 'info', 'warning', 'danger' (Bootstrap) vs 'error'
    - Fix: Standardize on Bootstrap categories

12. **No Logging Strategy**
    - Location: app.py:15 (basic config only)
    - Issue: Logs not structured or persisted
    - Fix: Add proper logging (rotation, levels, structured)

13. **No Database Backups**
    - Issue: No automated backup strategy
    - Impact: Data loss risk
    - Fix: Add backup script and cron job

14. **No Audit Trail**
    - Issue: No tracking of admin actions
    - Impact: Cannot trace data changes
    - Fix: Add AuditLog model

15. **Outdated Bootstrap 3**
    - Location: templates/, requirements.txt
    - Issue: Bootstrap 3 reached EOL in 2019
    - Impact: Security vulnerabilities, no modern features
    - Fix: Migrate to Bootstrap 5

### Low Priority Issues

16. **Mixed Language Comments**
    - Location: Throughout codebase
    - Issue: Serbian/Croatian comments in English codebase
    - Fix: Translate or document language policy

17. **No API Endpoints**
    - Issue: Cannot integrate with mobile apps
    - Fix: Add REST API layer

18. **No WebSocket for Chat**
    - Location: routes/chat.py
    - Issue: Polling-based chat (inefficient)
    - Fix: Implement WebSocket (Flask-SocketIO)

19. **No Image Optimization**
    - Location: Product/post image uploads
    - Issue: Large images slow page load
    - Fix: Add image processing (thumbnails, WebP)

20. **No Content Security Policy (CSP)**
    - Issue: XSS risk
    - Fix: Add CSP headers

---

## Improvement Recommendations

### Phase 1: Critical Fixes (1-2 weeks)

#### 1.1 Add Missing Dependencies
```bash
# Add to requirements.txt
pandas==2.1.4
openpyxl==3.1.2
Pillow==10.2.0  # For image processing
Flask-Limiter==3.5.0  # Rate limiting
```

#### 1.2 Fix Import Inconsistencies
```python
# In product.py:2
# BEFORE:
from app import db

# AFTER:
from extensions import db
```

#### 1.3 Add Environment Variable Validation
```python
# Create new file: env_validator.py
import os
import sys

REQUIRED_ENV_VARS = {
    'production': ['SESSION_SECRET', 'DATABASE_URL', 'STRIPE_API_KEY'],
    'development': [],
    'testing': []
}

def validate_environment(config_name):
    required = REQUIRED_ENV_VARS.get(config_name, [])
    missing = [var for var in required if not os.environ.get(var)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
```

#### 1.4 Add Basic Input Validation for Uploads
```python
# utils.py - Add new function
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_image_upload(file):
    """Validate uploaded image file"""
    if not file:
        return False, "No file provided"

    if file.filename == '':
        return False, "No file selected"

    # Check extension
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Use: {', '.join(ALLOWED_EXTENSIONS)}"

    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset

    if size > MAX_FILE_SIZE:
        return False, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"

    return True, None
```

### Phase 2: Testing Infrastructure (2-3 weeks)

#### 2.1 Create Test Structure
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_models.py           # Model tests
├── test_auth.py             # Authentication tests
├── test_product.py          # Product tests
├── test_cart.py             # Cart/checkout tests
├── test_admin.py            # Admin panel tests
├── test_pc_builder.py       # PC builder tests
└── test_utils.py            # Utility function tests
```

#### 2.2 Sample Test File (tests/conftest.py)
```python
import pytest
from app import create_app
from extensions import db
from models import User, Product, Category

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Authenticated test client"""
    # Create test user
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()

    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    return client

@pytest.fixture
def sample_products():
    """Create sample products for testing"""
    category = Category(name='CPUs', slug='cpus')
    db.session.add(category)
    db.session.flush()

    products = [
        Product(name='AMD Ryzen 5 5600X', price=199.99, stock=10, category_id=category.id, slug='amd-ryzen-5-5600x'),
        Product(name='Intel Core i5-12400F', price=179.99, stock=15, category_id=category.id, slug='intel-core-i5-12400f'),
    ]
    db.session.add_all(products)
    db.session.commit()

    return products
```

#### 2.3 Sample Test File (tests/test_cart.py)
```python
def test_view_cart_empty(auth_client):
    """Test viewing empty cart"""
    response = auth_client.get('/cart')
    assert response.status_code == 200
    assert b'Korpa' in response.data

def test_add_to_cart(auth_client, sample_products):
    """Test adding product to cart"""
    product = sample_products[0]
    response = auth_client.post('/cart/add', data={
        'product_id': product.id,
        'quantity': 2
    })
    assert response.status_code == 302  # Redirect

    # Verify cart contains item
    response = auth_client.get('/cart')
    assert product.name.encode() in response.data

def test_update_cart_quantity(auth_client, sample_products):
    """Test updating cart item quantity"""
    # Add item first
    product = sample_products[0]
    auth_client.post('/cart/add', data={'product_id': product.id, 'quantity': 1})

    # Update quantity
    cart_item = CartItem.query.filter_by(product_id=product.id).first()
    response = auth_client.post('/cart/update', json={
        str(cart_item.id): {'quantity': 3, 'extended_warranty': False}
    })

    data = response.get_json()
    assert data['success'] is True

def test_checkout_empty_cart(auth_client):
    """Test checkout with empty cart"""
    response = auth_client.get('/checkout')
    assert response.status_code == 302  # Redirect to cart
```

### Phase 3: Code Quality & Architecture (3-4 weeks)

#### 3.1 Create Service Layer
```python
# services/__init__.py
from .product_service import ProductService
from .cart_service import CartService
from .order_service import OrderService

# services/product_service.py
class ProductService:
    @staticmethod
    def get_products_by_category(category_slug, filters=None, page=1, per_page=12):
        """Get filtered and paginated products"""
        query = Product.query.filter(
            Product.stock > 0,
            Product.is_publicly_visible == True
        )

        if category_slug:
            category = Category.query.filter_by(slug=category_slug).first_or_404()
            category_ids = ProductService._get_child_category_ids(category)
            query = query.filter(Product.category_id.in_(category_ids))

        if filters:
            query = ProductService._apply_filters(query, filters)

        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def _get_child_category_ids(category):
        """Recursively get all child category IDs"""
        child_ids = [category.id]
        for child in category.subcategories:
            child_ids.extend(ProductService._get_child_category_ids(child))
        return child_ids

    @staticmethod
    def _apply_filters(query, filters):
        """Apply attribute filters to query"""
        # Implementation here
        return query

# Usage in routes/product.py
from services import ProductService

@product_bp.route('/products/<string:category_slug>')
def products(category_slug):
    filters = {
        'search': request.args.get('q'),
        'sort': request.args.get('sort', 'name_asc'),
        'attributes': json.loads(request.args.get('attr_filters', '{}'))
    }

    products = ProductService.get_products_by_category(
        category_slug,
        filters=filters,
        page=request.args.get('page', 1, type=int)
    )

    return render_template('shop/products.html', products=products)
```

#### 3.2 Add Structured Logging
```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_logging(app):
    """Configure application logging"""
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/sajborg.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Add to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sajborg startup')

# In app.py
from logging_config import setup_logging

def create_app(config_name='default'):
    app = Flask(__name__)
    # ... existing config ...
    setup_logging(app)
    return app
```

#### 3.3 Add Rate Limiting
```python
# In requirements.txt
Flask-Limiter==3.5.0

# In extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)  # NEW

# In routes/auth.py
from extensions import limiter

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Prevent brute force
def login():
    # ... existing code ...
```

### Phase 4: Performance Optimization (2-3 weeks)

#### 4.1 Add Query Optimization
```python
# In models.py - Add eager loading hints
class Product(db.Model):
    # ... existing fields ...

    @staticmethod
    def get_with_images():
        """Eager load product images to prevent N+1"""
        return Product.query.options(
            db.joinedload(Product.images),
            db.joinedload(Product.category)
        )

# In routes/product.py
products = Product.get_with_images().filter(...).paginate(...)
```

#### 4.2 Add Caching Layer
```python
# In requirements.txt
Flask-Caching==2.1.0

# In extensions.py
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'simple',  # Use Redis in production
    'CACHE_DEFAULT_TIMEOUT': 300
})

def init_extensions(app):
    # ... existing ...
    cache.init_app(app)

# In routes/product.py
from extensions import cache

@product_bp.route('/products/<string:category_slug>')
@cache.cached(timeout=300, query_string=True)
def products(category_slug):
    # ... existing code ...
```

#### 4.3 Add Database Indexing
```python
# Create migration: flask db revision -m "add_performance_indexes"

def upgrade():
    op.create_index('idx_product_category', 'product', ['category_id'])
    op.create_index('idx_product_visible_stock', 'product', ['is_publicly_visible', 'stock'])
    op.create_index('idx_product_slug', 'product', ['slug'])
    op.create_index('idx_category_slug', 'category', ['slug'])
    op.create_index('idx_order_user', 'order', ['user_id'])
    op.create_index('idx_order_status', 'order', ['status'])
    op.create_index('idx_review_product', 'review', ['product_id'])
    op.create_index('idx_cart_user', 'cart_item', ['user_id'])

def downgrade():
    op.drop_index('idx_cart_user', table_name='cart_item')
    op.drop_index('idx_review_product', table_name='review')
    op.drop_index('idx_order_status', table_name='order')
    op.drop_index('idx_order_user', table_name='order')
    op.drop_index('idx_category_slug', table_name='category')
    op.drop_index('idx_product_slug', table_name='product')
    op.drop_index('idx_product_visible_stock', table_name='product')
    op.drop_index('idx_product_category', table_name='product')
```

### Phase 5: Security Hardening (1-2 weeks)

#### 5.1 Add Content Security Policy
```python
# security.py
from flask import make_response

def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self' https://api.stripe.com; "
        "frame-src https://js.stripe.com;"
    )
    return response

# In app.py
@app.after_request
def after_request(response):
    return add_security_headers(response)
```

#### 5.2 Add Email Verification
```python
# Create verification model
class EmailVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

# In routes/auth.py
import secrets
from datetime import timedelta

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    verification = EmailVerification.query.filter_by(token=token).first_or_404()

    if verification.expires_at < datetime.utcnow():
        flash('Verification link has expired.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.get(verification.user_id)
    user.email_verified = True
    db.session.delete(verification)
    db.session.commit()

    flash('Email verified successfully!', 'success')
    return redirect(url_for('auth.login'))
```

#### 5.3 Add Audit Logging
```python
# models.py
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    changes = db.Column(db.Text, nullable=True)  # JSON
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# utils.py
def log_admin_action(user_id, action, table_name, record_id=None, changes=None):
    """Log admin actions for audit trail"""
    from flask import request

    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        changes=json.dumps(changes) if changes else None,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

# Usage in admin routes
log_admin_action(
    current_user.id,
    'DELETE_PRODUCT',
    'product',
    product.id,
    {'name': product.name}
)
```

### Phase 6: Modern Frontend (4-6 weeks)

#### 6.1 Migrate to Bootstrap 5
- Update Flask-Bootstrap to Bootstrap-Flask
- Rewrite templates for Bootstrap 5
- Update JavaScript for Bootstrap 5 API changes
- Test all UI components

#### 6.2 Add Build System
```bash
# Install Node.js dependencies
npm init -y
npm install --save-dev webpack webpack-cli babel-loader @babel/core @babel/preset-env
npm install --save-dev sass-loader css-loader style-loader mini-css-extract-plugin
npm install --save-dev terser-webpack-plugin

# webpack.config.js
module.exports = {
  entry: './static/js/main.js',
  output: {
    filename: 'bundle.js',
    path: path.resolve(__dirname, 'static/dist')
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: 'babel-loader'
      },
      {
        test: /\.scss$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader']
      }
    ]
  }
}
```

---

## Security Considerations

### Current Security Posture

**Implemented:**
- ✅ CSRF protection (Flask-WTF)
- ✅ Password hashing (bcrypt)
- ✅ SQL injection prevention (ORM)
- ✅ Session security (HTTPOnly, SameSite)
- ✅ Role-based access control
- ✅ User ban functionality

**Missing:**
- ❌ Rate limiting
- ❌ Content Security Policy
- ❌ Email verification
- ❌ File upload validation
- ❌ Audit logging
- ❌ HTTPS enforcement (production)
- ❌ Security headers (X-Frame-Options, etc.)
- ❌ Input sanitization (XSS prevention)
- ❌ Password strength requirements
- ❌ Account lockout after failed attempts

### Vulnerability Assessment

| Vulnerability | Risk Level | Current Status | Recommendation |
|---------------|-----------|----------------|----------------|
| XSS | Medium | Jinja2 auto-escaping | Add CSP headers |
| CSRF | Low | Protected | ✓ Good |
| SQL Injection | Low | ORM protection | ✓ Good |
| Brute Force | High | No protection | Add rate limiting |
| Session Hijacking | Medium | Secure cookies | Add HTTPS enforcement |
| File Upload | High | No validation | Add file type/size checks |
| Clickjacking | Medium | No protection | Add X-Frame-Options |
| Account Enumeration | Low | Generic messages | ✓ Good |
| Sensitive Data Exposure | Medium | No HTTPS enforcement | Force HTTPS in production |

### Security Checklist for Production

- [ ] Enable HTTPS and force SSL
- [ ] Set strong SESSION_SECRET (not default)
- [ ] Add rate limiting on all routes
- [ ] Implement CSP headers
- [ ] Add file upload validation
- [ ] Enable security headers (X-Frame-Options, etc.)
- [ ] Add audit logging for admin actions
- [ ] Implement email verification
- [ ] Add password strength requirements
- [ ] Set up automated security scanning (Bandit, Safety)
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable error logging (Sentry)
- [ ] Add monitoring (uptime, performance)
- [ ] Implement IP whitelisting for admin panel

---

## Performance Optimization Opportunities

### Database Optimization

1. **Add Indexes** (High Impact)
   - Product: category_id, slug, is_publicly_visible
   - Order: user_id, status
   - CartItem: user_id
   - Review: product_id
   - Estimated improvement: 50-70% faster queries

2. **Query Optimization** (High Impact)
   - Eager load relationships (joinedload)
   - Fix N+1 queries in product listing
   - Optimize recursive category queries
   - Estimated improvement: 40-60% faster page loads

3. **Database Upgrade** (Medium Impact)
   - Migrate SQLite → PostgreSQL
   - Enable connection pooling
   - Add query caching
   - Estimated improvement: 30-50% better concurrency

### Caching Strategy

1. **Page Caching** (High Impact)
   - Cache product listings (5 min TTL)
   - Cache category tree (1 hour TTL)
   - Cache featured products (15 min TTL)
   - Estimated improvement: 80-90% faster repeat visits

2. **Fragment Caching** (Medium Impact)
   - Cache product cards
   - Cache navigation menu
   - Cache footer content

3. **Redis Integration** (High Impact)
   - Session storage
   - Cache backend
   - Rate limiting storage
   - Message queue

### Frontend Optimization

1. **Image Optimization** (High Impact)
   - Generate thumbnails on upload
   - Convert to WebP format
   - Implement lazy loading
   - Add responsive images (srcset)
   - Estimated improvement: 60-80% faster page load

2. **Asset Bundling** (Medium Impact)
   - Minify JavaScript (9 files → 1 bundle)
   - Minify CSS (10 files → 1 bundle)
   - Add gzip compression
   - Estimated improvement: 40-60% smaller assets

3. **CDN Integration** (Medium Impact)
   - Serve static assets from CDN
   - Offload image hosting
   - Estimated improvement: 30-50% faster global access

### Application Performance

1. **Background Jobs** (High Impact)
   - Email sending
   - Image processing
   - Report generation
   - Use Celery + Redis

2. **API Optimization**
   - Add pagination to all lists
   - Implement GraphQL for flexible queries
   - Add API versioning

3. **Monitoring**
   - Add APM (Application Performance Monitoring)
   - Track slow queries
   - Monitor memory usage
   - Set up alerts

---

## Maintenance & Best Practices

### Code Style Guidelines

```python
# Use docstrings for all functions
def calculate_order_total(cart_items):
    """
    Calculate total order amount from cart items, including extended warranty.

    Args:
        cart_items (list): List of CartItem objects

    Returns:
        float: Total order amount rounded to 2 decimal places
    """
    total = 0
    for item in cart_items:
        item_price = item.product.price
        if item.extended_warranty:
            item_price *= 1.10
        total += item_price * item.quantity
    return round(total, 2)

# Use type hints
from typing import List, Optional, Dict

def get_products_by_category(
    category_id: int,
    filters: Optional[Dict] = None,
    page: int = 1
) -> List[Product]:
    """Get filtered products for a category"""
    pass

# Use constants instead of magic numbers
MAX_CART_ITEMS = 50
WARRANTY_MARKUP_PERCENT = 10
SHIPPING_COST_BAM = 10.0

# Follow PEP 8
# - 4 spaces for indentation
# - Max line length: 100 characters
# - Two blank lines between top-level functions
# - One blank line between methods
```

### Git Workflow

```bash
# Feature branch workflow
git checkout -b feature/add-wishlist
git commit -m "feat: add wishlist functionality"
git push origin feature/add-wishlist
# Create PR, review, merge

# Commit message format
# Type: feat, fix, docs, style, refactor, test, chore
# Examples:
# feat: add product comparison feature
# fix: resolve cart quantity validation bug
# docs: update README with deployment instructions
# refactor: extract order service layer
# test: add cart integration tests
```

### Database Migration Workflow

```bash
# Create migration
flask db migrate -m "add product comparison table"

# Review migration file in migrations/versions/
# Test in development
flask db upgrade

# Test rollback
flask db downgrade

# Apply in production (with backup first!)
pg_dump pcshop_prod > backup_$(date +%Y%m%d).sql
flask db upgrade
```

### Deployment Checklist

**Pre-Deployment:**
- [ ] Run all tests: `pytest`
- [ ] Check code quality: `flake8`, `pylint`
- [ ] Security scan: `bandit -r .`
- [ ] Dependency audit: `safety check`
- [ ] Database backup
- [ ] Update CHANGELOG.md
- [ ] Tag release: `git tag v1.2.3`

**Deployment:**
- [ ] Pull latest code
- [ ] Activate virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run migrations: `flask db upgrade`
- [ ] Collect static files (if applicable)
- [ ] Restart application server
- [ ] Clear cache
- [ ] Verify deployment (smoke tests)

**Post-Deployment:**
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify key features work
- [ ] Notify team

### Monitoring & Alerting

```python
# Set up Sentry for error tracking
# In requirements.txt
sentry-sdk[flask]==1.40.0

# In app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    environment=os.environ.get('FLASK_ENV', 'production')
)
```

### Backup Strategy

```bash
#!/bin/bash
# backup_db.sh - Daily database backup

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/pcshop"
DB_FILE="instance/pcshop.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# SQLite backup
sqlite3 $DB_FILE ".backup '$BACKUP_DIR/pcshop_$DATE.db'"

# Compress
gzip $BACKUP_DIR/pcshop_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "pcshop_*.db.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/pcshop_$DATE.db.gz s3://bucket/backups/
```

---

## Priority Action Items

### Immediate (This Week)

1. **Add missing dependencies to requirements.txt**
   - pandas, openpyxl, Pillow
   - Estimated time: 15 minutes

2. **Fix import inconsistencies**
   - Change `from app import db` to `from extensions import db` in product.py
   - Estimated time: 5 minutes

3. **Add basic file upload validation**
   - Implement `validate_image_upload()` function
   - Apply to product image uploads
   - Estimated time: 2 hours

4. **Set up proper environment variable handling**
   - Create .env.example
   - Document required variables
   - Add validation in production
   - Estimated time: 1 hour

### Short-term (Next 2 Weeks)

5. **Add basic test suite**
   - Set up pytest fixtures
   - Write 20-30 critical tests
   - Estimated time: 16 hours

6. **Add rate limiting**
   - Install Flask-Limiter
   - Add limits to login, registration, checkout
   - Estimated time: 4 hours

7. **Implement structured logging**
   - Set up rotating file handler
   - Add log levels
   - Estimated time: 3 hours

8. **Add database indexes**
   - Create migration with indexes
   - Test performance improvement
   - Estimated time: 2 hours

### Medium-term (Next Month)

9. **Create service layer**
   - Extract business logic from routes
   - Create ProductService, OrderService, etc.
   - Estimated time: 40 hours

10. **Add caching layer**
    - Install Flask-Caching
    - Cache product listings, categories
    - Estimated time: 8 hours

11. **Security hardening**
    - Add CSP headers
    - Implement email verification
    - Add audit logging
    - Estimated time: 20 hours

12. **Performance optimization**
    - Fix N+1 queries
    - Add eager loading
    - Optimize images
    - Estimated time: 16 hours

### Long-term (Next Quarter)

13. **Migrate to Bootstrap 5**
    - Update all templates
    - Rewrite custom CSS
    - Test all pages
    - Estimated time: 60 hours

14. **Add API layer**
    - Design RESTful API
    - Add authentication (JWT)
    - Document endpoints
    - Estimated time: 80 hours

15. **Comprehensive testing**
    - Achieve 80%+ code coverage
    - Add integration tests
    - Add E2E tests (Selenium/Playwright)
    - Estimated time: 100 hours

---

## Conclusion

The **Sajborg.com** codebase is a solid foundation for an e-commerce platform with good architectural decisions and comprehensive features. The main areas needing improvement are:

1. **Testing** - Zero coverage is the biggest risk
2. **Security** - Missing rate limiting, file validation, CSP
3. **Performance** - No caching, unoptimized queries
4. **Code Organization** - Business logic in routes, no service layer
5. **Dependencies** - Outdated Bootstrap, missing packages

Following the phased improvement plan above will transform this into a production-ready, maintainable, and scalable application.

**Estimated Total Effort:**
- Critical fixes: 1-2 weeks
- Testing infrastructure: 2-3 weeks
- Code quality: 3-4 weeks
- Performance: 2-3 weeks
- Security: 1-2 weeks
- Frontend modernization: 4-6 weeks

**Total: 13-20 weeks** for full implementation (with 1-2 developers)

---

## Appendix

### Useful Commands

```bash
# Development
flask run --debug
flask shell
flask db migrate -m "description"
flask db upgrade
flask db downgrade

# Testing
pytest
pytest --cov=. --cov-report=html
pytest -v -s tests/test_cart.py

# Code Quality
flake8 .
pylint *.py routes/ models.py
black .  # Code formatter
isort .  # Import sorter

# Security
bandit -r .
safety check

# Database
flask db current
flask db history
sqlite3 instance/pcshop.db ".tables"
sqlite3 instance/pcshop.db ".schema product"

# Production
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Flask Testing: https://flask.palletsprojects.com/en/latest/testing/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Python Testing with pytest: https://docs.pytest.org/

---

**Document Version:** 1.0
**Last Updated:** 2025-01-13
**Author:** Claude Code Analysis
**Status:** Active
