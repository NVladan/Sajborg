"""
Unit tests for database models.

Tests cover:
- User model (authentication, roles)
- Product model (properties, relationships)
- Category model (hierarchy)
- Order model (calculations)
- Cart model
- Review model
"""

import pytest
from datetime import datetime

from models import User, Product, Category, Order, CartItem, Review


# =============================================================================
# User Model Tests
# =============================================================================

@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""

    def test_create_user(self, app):
        """Test user creation."""
        with app.app_context():
            from extensions import db
            user = User(
                username='newuser',
                email='new@example.com',
                role='musterija'
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == 'newuser'
            assert user.role == 'musterija'

    def test_password_hashing(self, sample_user):
        """Test password is hashed, not stored as plaintext."""
        assert sample_user.password_hash != 'Password123'
        assert sample_user.check_password('Password123') is True
        assert sample_user.check_password('wrongpassword') is False

    def test_user_repr(self, sample_user):
        """Test user string representation."""
        assert repr(sample_user) == '<User testuser>'

    def test_user_roles(self, app):
        """Test different user roles."""
        with app.app_context():
            from extensions import db
            roles = ['admin', 'dobavljac', 'distributer', 'musterija']
            for role in roles:
                user = User(
                    username=f'user_{role}',
                    email=f'{role}@example.com',
                    role=role
                )
                user.set_password('password')
                db.session.add(user)
            db.session.commit()

            admin = User.query.filter_by(role='admin').first()
            assert admin.role == 'admin'

    def test_user_default_role(self, app):
        """Test default role is 'musterija'."""
        with app.app_context():
            from extensions import db
            user = User(username='notrole', email='norole@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()

            assert user.role == 'musterija'

    def test_user_ban_status(self, app):
        """Test user ban functionality."""
        with app.app_context():
            from extensions import db
            user = User(username='baduser', email='bad@example.com', is_banned=False)
            user.set_password('password')
            db.session.add(user)
            db.session.flush()
            assert user.is_banned is False

            user.is_banned = True
            db.session.commit()

            banned_user = User.query.filter_by(username='baduser').first()
            assert banned_user.is_banned is True

    def test_user_subscription(self, sample_user):
        """Test newsletter subscription."""
        assert sample_user.is_subscribed is False


# =============================================================================
# Product Model Tests
# =============================================================================

@pytest.mark.unit
class TestProductModel:
    """Test Product model functionality."""

    def test_create_product(self, app, sample_category):
        """Test product creation."""
        with app.app_context():
            from extensions import db
            product = Product(
                name='Test Product',
                slug='test-product',
                description='A test product',
                price=99.99,
                stock=10,
                category_id=sample_category.id,
                condition='Novo',
                availability='Dostupno odmah'
            )
            db.session.add(product)
            db.session.commit()

            assert product.id is not None
            assert product.name == 'Test Product'
            assert product.price == 99.99

    def test_product_repr(self, sample_product):
        """Test product string representation."""
        assert 'Ryzen' in repr(sample_product)

    def test_product_default_condition(self, app, sample_category):
        """Test product default condition is 'Novo'."""
        with app.app_context():
            from extensions import db
            product = Product(
                name='New Product',
                slug='new-product',
                price=100.0,
                category_id=sample_category.id
            )
            db.session.add(product)
            db.session.commit()

            assert product.condition == 'Novo'

    def test_product_visibility(self, sample_product):
        """Test product visibility flag."""
        assert sample_product.is_publicly_visible is True

    def test_product_average_rating_no_reviews(self, sample_product):
        """Test average rating with no reviews."""
        assert sample_product.average_rating == 0

    def test_product_average_rating_with_reviews(self, app, sample_product, sample_user):
        """Test average rating calculation."""
        with app.app_context():
            from extensions import db
            # Add reviews
            review1 = Review(
                rating=5,
                text='Great product',
                user_id=sample_user.id,
                product_id=sample_product.id
            )
            review2 = Review(
                rating=3,
                text='Okay product',
                user_id=sample_user.id,
                product_id=sample_product.id
            )
            db.session.add_all([review1, review2])
            db.session.commit()

            # Refresh product to get reviews
            product = Product.query.get(sample_product.id)
            assert product.average_rating == 4.0  # (5 + 3) / 2

    def test_product_timestamps(self, sample_product):
        """Test product has timestamps."""
        assert sample_product.created_at is not None
        assert isinstance(sample_product.created_at, datetime)


# =============================================================================
# Category Model Tests
# =============================================================================

@pytest.mark.unit
class TestCategoryModel:
    """Test Category model functionality."""

    def test_create_category(self, app):
        """Test category creation."""
        with app.app_context():
            from extensions import db
            category = Category(
                name='Test Category',
                slug='test-category',
                is_public=True
            )
            db.session.add(category)
            db.session.commit()

            assert category.id is not None
            assert category.name == 'Test Category'

    def test_category_hierarchy(self, app):
        """Test parent-child category relationships."""
        with app.app_context():
            from extensions import db
            parent = Category(name='Electronics', slug='electronics', is_public=True)
            db.session.add(parent)
            db.session.commit()

            child = Category(
                name='Computers',
                slug='computers',
                parent_id=parent.id,
                is_public=True
            )
            db.session.add(child)
            db.session.commit()

            # Test relationships
            parent_cat = Category.query.filter_by(slug='electronics').first()
            assert len(parent_cat.subcategories) == 1
            assert parent_cat.subcategories[0].name == 'Computers'

            child_cat = Category.query.filter_by(slug='computers').first()
            assert child_cat.parent.name == 'Electronics'

    def test_category_visibility(self, app):
        """Test category public/private visibility."""
        with app.app_context():
            from extensions import db
            public_cat = Category(name='Public', slug='public', is_public=True)
            private_cat = Category(name='Private', slug='private', is_public=False)
            db.session.add_all([public_cat, private_cat])
            db.session.commit()

            public_categories = Category.query.filter_by(is_public=True).all()
            assert len(public_categories) >= 1

    def test_category_repr(self, sample_category):
        """Test category string representation."""
        assert 'Procesori' in repr(sample_category)


# =============================================================================
# Cart Model Tests
# =============================================================================

@pytest.mark.unit
class TestCartModel:
    """Test CartItem model functionality."""

    def test_create_cart_item(self, app, sample_user, sample_product):
        """Test cart item creation."""
        with app.app_context():
            from extensions import db
            cart_item = CartItem(
                user_id=sample_user.id,
                product_id=sample_product.id,
                quantity=2
            )
            db.session.add(cart_item)
            db.session.commit()

            assert cart_item.id is not None
            assert cart_item.quantity == 2

    def test_cart_item_default_quantity(self, app, sample_user, sample_product):
        """Test default quantity is 1."""
        with app.app_context():
            from extensions import db
            cart_item = CartItem(
                user_id=sample_user.id,
                product_id=sample_product.id
            )
            db.session.add(cart_item)
            db.session.commit()

            assert cart_item.quantity == 1

    def test_cart_item_extended_warranty(self, sample_cart_item):
        """Test extended warranty flag."""
        assert sample_cart_item.extended_warranty is False

    def test_cart_item_relationships(self, app, sample_cart_item):
        """Test cart item relationships."""
        with app.app_context():
            from extensions import db
            # Refresh the cart item to bind it to the current session
            cart_item = db.session.merge(sample_cart_item)
            db.session.refresh(cart_item)
            assert cart_item.user is not None
            assert cart_item.product is not None
            assert cart_item.user.username == 'testuser'


# =============================================================================
# Order Model Tests
# =============================================================================

@pytest.mark.unit
class TestOrderModel:
    """Test Order model functionality."""

    def test_create_order(self, sample_order):
        """Test order creation."""
        assert sample_order.id is not None
        assert sample_order.total_amount == 599.98
        assert sample_order.status == 'pending'

    def test_order_default_payment_method(self, app, sample_user):
        """Test default payment method."""
        with app.app_context():
            from extensions import db
            order = Order(
                user_id=sample_user.id,
                total_amount=100.0
            )
            db.session.add(order)
            db.session.commit()

            assert order.payment_method == 'cash_on_delivery'

    def test_order_shipping_address(self, sample_order):
        """Test full shipping address property."""
        address = sample_order.full_shipping_address
        assert 'Test User' in address
        assert '123 Test St' in address
        assert 'Sarajevo' in address
        assert '+387 61 123 456' in address

    def test_order_timestamps(self, sample_order):
        """Test order has timestamps."""
        assert sample_order.created_at is not None
        assert isinstance(sample_order.created_at, datetime)

    def test_order_products_relationship(self, sample_order):
        """Test order products many-to-many relationship."""
        assert len(sample_order.products) >= 1


# =============================================================================
# Review Model Tests
# =============================================================================

@pytest.mark.unit
class TestReviewModel:
    """Test Review model functionality."""

    def test_create_review(self, app, sample_user, sample_product):
        """Test review creation."""
        with app.app_context():
            from extensions import db
            review = Review(
                rating=5,
                text='Excellent product!',
                user_id=sample_user.id,
                product_id=sample_product.id
            )
            db.session.add(review)
            db.session.commit()

            assert review.id is not None
            assert review.rating == 5

    def test_review_repr(self, app, sample_user, sample_product):
        """Test review string representation."""
        with app.app_context():
            from extensions import db
            review = Review(
                rating=4,
                text='Good',
                user_id=sample_user.id,
                product_id=sample_product.id
            )
            db.session.add(review)
            db.session.commit()

            assert 'testuser' in repr(review)
            assert 'Ryzen' in repr(review)

    def test_review_relationships(self, app, sample_user, sample_product):
        """Test review relationships."""
        with app.app_context():
            from extensions import db
            review = Review(
                rating=5,
                text='Great!',
                user_id=sample_user.id,
                product_id=sample_product.id
            )
            db.session.add(review)
            db.session.commit()

            assert review.author.username == 'testuser'
            assert 'Ryzen' in review.product.name

    def test_review_optional_order(self, app, sample_user, sample_product, sample_order):
        """Test review can be linked to order (verified purchase)."""
        with app.app_context():
            from extensions import db
            review = Review(
                rating=5,
                text='Verified purchase review',
                user_id=sample_user.id,
                product_id=sample_product.id,
                order_id=sample_order.id
            )
            db.session.add(review)
            db.session.commit()

            assert review.order_id == sample_order.id
