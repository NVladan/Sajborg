"""
Pytest configuration and shared fixtures.

This file contains all shared test fixtures that can be used across test files.
"""

import pytest
import os
import tempfile
from io import BytesIO
from werkzeug.datastructures import FileStorage

from app import create_app
from extensions import db
from models import (
    User, Product, Category, CartItem, Order, order_items,
    PCBuild, Review, Post, LagerProduct, LagerCategory
)


@pytest.fixture(scope='session')
def app():
    """
    Create application for testing with test configuration.
    Session-scoped: Created once for entire test session.
    """
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()

    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key',
        'RATELIMIT_ENABLED': False  # Disable rate limiting for testing
    })

    # Create database tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """
    Test client for making requests.
    Function-scoped: Fresh client for each test.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function', autouse=True)
def db_session(app):
    """
    Database session for tests.
    Automatically rolls back after each test.
    Auto-used by all tests to ensure cleanup.
    """
    with app.app_context():
        # Ensure we start fresh
        yield db.session

        # Rollback any changes made during the test
        db.session.rollback()
        # Remove all data from all tables
        db.session.remove()
        # Delete all records from tables (but keep schema)
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def sample_user(app):
    """Create a sample regular user."""
    with app.app_context():
        # Check if user already exists (from previous test)
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            return existing_user

        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='musterija'
        )
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()
        # Refresh to get the ID
        db.session.refresh(user)
        return user


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        # Check if admin already exists (from previous test)
        existing_admin = User.query.filter_by(email='admin@example.com').first()
        if existing_admin:
            return existing_admin

        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password('Admin123')
        db.session.add(admin)
        db.session.commit()
        # Refresh to get the ID
        db.session.refresh(admin)
        return admin


@pytest.fixture
def auth_client(client, sample_user):
    """Authenticated test client (logged in as regular user)."""
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'Password123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Authenticated test client (logged in as admin)."""
    client.post('/login', data={
        'email': 'admin@example.com',
        'password': 'Admin123'
    }, follow_redirects=True)
    return client


# =============================================================================
# Category Fixtures
# =============================================================================

@pytest.fixture
def sample_category(app):
    """Create a sample category."""
    with app.app_context():
        # Check if category already exists
        existing = Category.query.filter_by(slug='procesori').first()
        if existing:
            db.session.refresh(existing)
            return existing

        category = Category(
            name='Procesori',
            slug='procesori',
            description='CPU procesori',
            component_type='CPU',
            is_public=True
        )
        db.session.add(category)
        db.session.commit()
        # Refresh to ensure it's bound to session
        db.session.refresh(category)
        return category


@pytest.fixture
def sample_categories(app):
    """Create multiple categories for testing."""
    with app.app_context():
        # Check for existing categories first
        slugs = ['cpus', 'gpus', 'ram', 'storage']
        existing_categories = Category.query.filter(Category.slug.in_(slugs)).all()

        if len(existing_categories) == 4:
            # Refresh all to bind to session
            for cat in existing_categories:
                db.session.refresh(cat)
            return existing_categories

        # Create missing categories
        categories_data = [
            {'name': 'CPUs', 'slug': 'cpus', 'component_type': 'CPU', 'is_public': True},
            {'name': 'GPUs', 'slug': 'gpus', 'component_type': 'GPU', 'is_public': True},
            {'name': 'RAM', 'slug': 'ram', 'component_type': 'RAM', 'is_public': True},
            {'name': 'Storage', 'slug': 'storage', 'component_type': 'Storage', 'is_public': True},
        ]

        categories = []
        for data in categories_data:
            existing = Category.query.filter_by(slug=data['slug']).first()
            if existing:
                db.session.refresh(existing)
                categories.append(existing)
            else:
                cat = Category(**data)
                db.session.add(cat)
                categories.append(cat)

        db.session.commit()
        # Refresh all to ensure they're bound
        for cat in categories:
            db.session.refresh(cat)
        return categories


# =============================================================================
# Product Fixtures
# =============================================================================

@pytest.fixture
def sample_product(app, sample_category):
    """Create a sample product."""
    with app.app_context():
        # Ensure category is in the current session
        category = db.session.merge(sample_category)

        # Check if product already exists
        existing = Product.query.filter_by(slug='amd-ryzen-5-5600x').first()
        if existing:
            db.session.refresh(existing)
            return existing

        product = Product(
            name='AMD Ryzen 5 5600X',
            slug='amd-ryzen-5-5600x',
            description='6-core 12-thread processor',
            price=299.99,
            stock=10,
            category_id=category.id,
            component_type='CPU',
            condition='Novo',
            availability='Dostupno odmah',
            is_publicly_visible=True
        )
        db.session.add(product)
        db.session.commit()
        # Refresh to ensure it's bound to session
        db.session.refresh(product)
        return product


@pytest.fixture
def sample_products(app, sample_categories):
    """Create multiple products for testing."""
    with app.app_context():
        # Ensure categories are in the current session
        categories = [db.session.merge(cat) for cat in sample_categories]

        # Check for existing products first
        slugs = ['amd-ryzen-5-5600x', 'intel-core-i5-12400f', 'nvidia-rtx-3060', 'out-of-stock']
        existing_products = Product.query.filter(Product.slug.in_(slugs)).all()

        if len(existing_products) == 4:
            # Refresh all to bind to session
            for prod in existing_products:
                db.session.refresh(prod)
            return existing_products

        # Create missing products
        products_data = [
            {
                'name': 'AMD Ryzen 5 5600X',
                'slug': 'amd-ryzen-5-5600x',
                'description': '6-core CPU',
                'price': 299.99,
                'stock': 10,
                'category_id': categories[0].id,
                'component_type': 'CPU',
                'condition': 'Novo',
                'availability': 'Dostupno odmah',
                'is_publicly_visible': True
            },
            {
                'name': 'Intel Core i5-12400F',
                'slug': 'intel-core-i5-12400f',
                'description': '6-core CPU',
                'price': 199.99,
                'stock': 15,
                'category_id': categories[0].id,
                'component_type': 'CPU',
                'condition': 'Novo',
                'availability': 'Dostupno odmah',
                'is_publicly_visible': True
            },
            {
                'name': 'NVIDIA RTX 3060',
                'slug': 'nvidia-rtx-3060',
                'description': 'Graphics card',
                'price': 399.99,
                'stock': 5,
                'category_id': categories[1].id,
                'component_type': 'GPU',
                'condition': 'Novo',
                'availability': 'Dostupno odmah',
                'is_publicly_visible': True
            },
            {
                'name': 'Out of Stock Item',
                'slug': 'out-of-stock',
                'description': 'No stock',
                'price': 99.99,
                'stock': 0,
                'category_id': categories[2].id,
                'component_type': 'RAM',
                'condition': 'Novo',
                'availability': 'Po narudžbi',
                'is_publicly_visible': False
            },
        ]

        products = []
        for data in products_data:
            existing = Product.query.filter_by(slug=data['slug']).first()
            if existing:
                db.session.refresh(existing)
                products.append(existing)
            else:
                prod = Product(**data)
                db.session.add(prod)
                products.append(prod)

        db.session.commit()
        # Refresh all to ensure they're bound
        for prod in products:
            db.session.refresh(prod)
        return products


# =============================================================================
# Cart Fixtures
# =============================================================================

@pytest.fixture
def sample_cart_item(app, sample_user, sample_product):
    """Create a cart item."""
    with app.app_context():
        # Ensure user and product are in the current session
        user = db.session.merge(sample_user)
        product = db.session.merge(sample_product)

        # Check if cart item already exists
        existing = CartItem.query.filter_by(user_id=user.id, product_id=product.id).first()
        if existing:
            db.session.refresh(existing)
            return existing

        cart_item = CartItem(
            user_id=user.id,
            product_id=product.id,
            quantity=2
        )
        db.session.add(cart_item)
        db.session.commit()
        db.session.refresh(cart_item)
        return cart_item


@pytest.fixture
def sample_cart(app, sample_user, sample_products):
    """Create a cart with multiple items."""
    with app.app_context():
        # Ensure user and products are in the current session
        user = db.session.merge(sample_user)
        products = [db.session.merge(prod) for prod in sample_products]

        # Check for existing cart items
        existing_items = CartItem.query.filter_by(user_id=user.id).all()
        if len(existing_items) >= 2:
            for item in existing_items:
                db.session.refresh(item)
            return existing_items[:2]

        # Delete any existing cart items for this user to start fresh
        CartItem.query.filter_by(user_id=user.id).delete()

        cart_items = [
            CartItem(user_id=user.id, product_id=products[0].id, quantity=1),
            CartItem(user_id=user.id, product_id=products[1].id, quantity=2),
        ]
        db.session.add_all(cart_items)
        db.session.commit()
        # Refresh all to ensure they're bound
        for item in cart_items:
            db.session.refresh(item)
        return cart_items


# =============================================================================
# Order Fixtures
# =============================================================================

@pytest.fixture
def sample_order(app, sample_user, sample_products):
    """Create a sample order."""
    with app.app_context():
        # Ensure user and products are in the current session
        user = db.session.merge(sample_user)
        products = [db.session.merge(prod) for prod in sample_products]

        # Check if order already exists for this user
        existing = Order.query.filter_by(user_id=user.id).first()
        if existing:
            db.session.refresh(existing)
            return existing

        order = Order(
            user_id=user.id,
            total_amount=599.98,
            status='pending',
            payment_method='cash_on_delivery',
            shipping_first_name='Test',
            shipping_last_name='User',
            shipping_address='123 Test St',
            shipping_city='Sarajevo',
            shipping_postal_code='71000',
            shipping_country='Bosnia and Herzegovina',
            shipping_phone_number='+387 61 123 456'
        )
        db.session.add(order)
        db.session.flush()

        # Add order items
        stmt = order_items.insert().values(
            order_id=order.id,
            product_id=products[0].id,
            quantity=2,
            price=products[0].price
        )
        db.session.execute(stmt)
        db.session.commit()
        db.session.refresh(order)
        return order


# =============================================================================
# File Upload Fixtures
# =============================================================================

@pytest.fixture
def mock_image_file():
    """Create a mock image file for upload testing."""
    return FileStorage(
        stream=BytesIO(b"fake image content here"),
        filename="test_image.jpg",
        content_type="image/jpeg"
    )


@pytest.fixture
def mock_large_file():
    """Create a mock large file (>5MB) for testing size validation."""
    # Create 6MB of data
    large_data = b"x" * (6 * 1024 * 1024)
    return FileStorage(
        stream=BytesIO(large_data),
        filename="large_image.jpg",
        content_type="image/jpeg"
    )


@pytest.fixture
def mock_invalid_file():
    """Create a mock invalid file (wrong extension)."""
    return FileStorage(
        stream=BytesIO(b"fake exe content"),
        filename="malware.exe",
        content_type="application/x-msdownload"
    )


@pytest.fixture
def mock_empty_file():
    """Create a mock empty file."""
    return FileStorage(
        stream=BytesIO(b""),
        filename="empty.jpg",
        content_type="image/jpeg"
    )


# =============================================================================
# Blog Fixtures
# =============================================================================

@pytest.fixture
def sample_post(app, admin_user):
    """Create a sample blog post."""
    with app.app_context():
        post = Post(
            title='Test Blog Post',
            slug='test-blog-post',
            content='This is test content',
            author_id=admin_user.id,
            is_published=True
        )
        db.session.add(post)
        db.session.commit()
        return post


# =============================================================================
# Helper Functions
# =============================================================================

def login(client, username, password):
    """Helper to login a user."""
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def logout(client):
    """Helper to logout a user."""
    return client.get('/auth/logout', follow_redirects=True)


@pytest.fixture
def login_helper():
    """Provide login helper function."""
    return login


@pytest.fixture
def logout_helper():
    """Provide logout helper function."""
    return logout
