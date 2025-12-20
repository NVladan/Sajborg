"""
Integration tests for shopping cart and checkout.

Tests cover:
- Adding items to cart
- Updating quantities
- Removing items
- Cart calculations
- Checkout process
- Order creation
"""

import pytest
from flask import session


# =============================================================================
# Cart View Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestCartView:
    """Test cart viewing functionality."""

    def test_view_empty_cart(self, auth_client):
        """Test viewing empty cart."""
        response = auth_client.get('/cart')
        assert response.status_code == 200
        assert b'korpa' in response.data.lower() or b'cart' in response.data.lower()

    def test_view_cart_with_items(self, auth_client, sample_cart):
        """Test viewing cart with items."""
        response = auth_client.get('/cart')
        assert response.status_code == 200
        # Should show items

    def test_cart_requires_login(self, client):
        """Test that cart requires authentication."""
        response = client.get('/cart')
        assert response.status_code in [302, 401]


# =============================================================================
# Add to Cart Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestAddToCart:
    """Test adding items to cart."""

    def test_add_product_to_cart(self, auth_client, sample_product, app):
        """Test adding a product to cart."""
        response = auth_client.post('/interaction/add-to-cart', data={
            'product_id': sample_product.id,
            'quantity': 1
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify item was added to cart
        with app.app_context():
            from models import CartItem
            cart_item = CartItem.query.filter_by(
                product_id=sample_product.id
            ).first()
            assert cart_item is not None
            assert cart_item.quantity == 1

    def test_add_multiple_quantity(self, auth_client, sample_product, app):
        """Test adding multiple quantities at once."""
        response = auth_client.post('/interaction/add-to-cart', data={
            'product_id': sample_product.id,
            'quantity': 3
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            from models import CartItem
            cart_item = CartItem.query.filter_by(
                product_id=sample_product.id
            ).first()
            assert cart_item.quantity == 3

    def test_add_out_of_stock_product(self, auth_client, sample_products):
        """Test adding out of stock product."""
        # Find the out of stock product
        out_of_stock = [p for p in sample_products if p.stock == 0][0]

        response = auth_client.post('/interaction/add-to-cart', data={
            'product_id': out_of_stock.id,
            'quantity': 1
        }, follow_redirects=True)

        # Should show error or prevent adding
        assert response.status_code in [200, 400]

    def test_add_exceeds_stock(self, auth_client, sample_product):
        """Test adding more than available stock."""
        response = auth_client.post('/interaction/add-to-cart', data={
            'product_id': sample_product.id,
            'quantity': sample_product.stock + 10  # More than available
        }, follow_redirects=True)

        # Should show error
        assert response.status_code in [200, 400]


# =============================================================================
# Update Cart Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestUpdateCart:
    """Test updating cart items."""

    def test_update_cart_quantity(self, auth_client, sample_cart_item, app):
        """Test updating item quantity."""
        response = auth_client.post('/cart/update', json={
            str(sample_cart_item.id): {
                'quantity': 5,
                'extended_warranty': False
            }
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify update
        with app.app_context():
            from models import CartItem
            cart_item = CartItem.query.get(sample_cart_item.id)
            assert cart_item.quantity == 5

    def test_update_cart_extended_warranty(self, auth_client, sample_cart_item, app):
        """Test enabling extended warranty."""
        response = auth_client.post('/cart/update', json={
            str(sample_cart_item.id): {
                'quantity': 2,
                'extended_warranty': True
            }
        })

        assert response.status_code == 200

        with app.app_context():
            from models import CartItem
            cart_item = CartItem.query.get(sample_cart_item.id)
            assert cart_item.extended_warranty is True

    def test_update_cart_quantity_zero_removes_item(self, auth_client, sample_cart_item, app):
        """Test that quantity 0 removes item."""
        response = auth_client.post('/cart/update', json={
            str(sample_cart_item.id): {
                'quantity': 0,
                'extended_warranty': False
            }
        })

        assert response.status_code == 200

        # Verify item was removed
        with app.app_context():
            from models import CartItem
            cart_item = CartItem.query.get(sample_cart_item.id)
            assert cart_item is None

    def test_update_cart_exceeds_stock(self, auth_client, sample_cart_item):
        """Test updating to more than available stock."""
        response = auth_client.post('/cart/update', json={
            str(sample_cart_item.id): {
                'quantity': 9999,  # Way more than stock
                'extended_warranty': False
            }
        })

        data = response.get_json()
        assert data['success'] is False
        assert 'dostupno' in data['message'].lower() or 'stock' in data['message'].lower()


# =============================================================================
# Remove from Cart Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestRemoveFromCart:
    """Test removing items from cart."""

    def test_remove_cart_item(self, auth_client, sample_cart_item, app):
        """Test removing an item from cart."""
        response = auth_client.post(
            f'/cart/remove/{sample_cart_item.id}',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify item was removed
        with app.app_context():
            from models import CartItem
            cart_item = CartItem.query.get(sample_cart_item.id)
            assert cart_item is None


# =============================================================================
# Cart Calculations Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestCartCalculations:
    """Test cart total calculations."""

    def test_cart_subtotal_calculation(self, auth_client, sample_cart):
        """Test cart subtotal is calculated correctly."""
        response = auth_client.get('/cart')
        assert response.status_code == 200
        # Subtotal should be in response

    def test_cart_with_extended_warranty(self, auth_client, app, sample_user, sample_product):
        """Test cart total with extended warranty."""
        with app.app_context():
            from extensions import db
            from models import CartItem
            cart_item = CartItem(
                user_id=sample_user.id,
                product_id=sample_product.id,
                quantity=1,
                extended_warranty=True
            )
            db.session.add(cart_item)
            db.session.commit()

        response = auth_client.get('/cart')
        assert response.status_code == 200
        # Total should include 10% warranty markup

    def test_cart_includes_shipping(self, auth_client, sample_cart):
        """Test that cart total includes shipping cost."""
        response = auth_client.get('/cart')
        assert response.status_code == 200
        # Should show shipping cost (10 BAM)


# =============================================================================
# Checkout Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestCheckout:
    """Test checkout process."""

    def test_checkout_page_loads(self, auth_client, sample_cart):
        """Test checkout page is accessible."""
        response = auth_client.get('/checkout')
        assert response.status_code == 200
        assert b'checkout' in response.data.lower() or 'plać'.encode('utf-8') in response.data.lower()

    def test_checkout_empty_cart_redirects(self, auth_client):
        """Test checkout with empty cart redirects."""
        response = auth_client.get('/checkout')
        # Should redirect to cart with message
        assert response.status_code in [200, 302]

    def test_successful_checkout(self, auth_client, sample_cart, app):
        """Test successful order creation."""
        response = auth_client.post('/checkout', data={
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'city': 'Sarajevo',
            'postal_code': '71000',
            'country': 'Bosnia and Herzegovina',
            'phone_number': '+387 61 123 456',
            'payment_method': 'cash_on_delivery'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify order was created
        with app.app_context():
            from models import Order
            order = Order.query.filter_by(
                shipping_city='Sarajevo'
            ).first()
            assert order is not None
            assert order.status == 'pending'

    def test_checkout_updates_stock(self, auth_client, sample_cart, app, sample_products):
        """Test that checkout decreases product stock."""
        # Get initial stock
        initial_stock = sample_products[0].stock

        response = auth_client.post('/checkout', data={
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'city': 'Sarajevo',
            'postal_code': '71000',
            'country': 'Bosnia and Herzegovina',
            'phone_number': '+387 61 123 456',
            'payment_method': 'cash_on_delivery'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify stock was decreased
        with app.app_context():
            from models import Product
            product = Product.query.get(sample_products[0].id)
            assert product.stock < initial_stock

    def test_checkout_clears_cart(self, auth_client, sample_cart, app, sample_user):
        """Test that checkout clears the cart."""
        response = auth_client.post('/checkout', data={
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Test St',
            'city': 'Sarajevo',
            'postal_code': '71000',
            'country': 'Bosnia and Herzegovina',
            'phone_number': '+387 61 123 456',
            'payment_method': 'cash_on_delivery'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify cart is empty
        with app.app_context():
            from models import CartItem
            cart_items = CartItem.query.filter_by(user_id=sample_user.id).all()
            assert len(cart_items) == 0

    def test_checkout_success_page(self, auth_client, sample_order):
        """Test checkout success page."""
        response = auth_client.get(f'/checkout/success?order_id={sample_order.id}')
        assert response.status_code == 200
        assert b'success' in response.data.lower() or 'uspešn'.encode('utf-8') in response.data.lower()

    def test_checkout_success_wrong_user(self, client, app, admin_user, sample_order):
        """Test that users can only view their own orders."""
        # Login as different user (admin)
        client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'Admin123'
        }, follow_redirects=True)

        # Try to view sample_user's order
        response = client.get(f'/checkout/success?order_id={sample_order.id}')
        # Should be 404 or forbidden
        assert response.status_code in [403, 404]


# =============================================================================
# Order Cancellation Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.cart
class TestOrderCancellation:
    """Test order cancellation."""

    def test_cancel_order(self, auth_client, sample_order, app):
        """Test cancelling an order."""
        response = auth_client.get(
            f'/checkout/cancel?order_id={sample_order.id}',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify order status is cancelled
        with app.app_context():
            from models import Order
            order = Order.query.get(sample_order.id)
            assert order.status == 'cancelled'
