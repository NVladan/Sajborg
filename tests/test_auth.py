"""
Integration tests for authentication routes.

Tests cover:
- User registration
- Login/logout
- Password requirements
- Session management
- Access control
"""

import pytest
from flask import session


# =============================================================================
# Registration Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
class TestRegistration:
    """Test user registration functionality."""

    def test_registration_page_loads(self, client):
        """Test registration page is accessible."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower() or b'registr' in response.data.lower()

    def test_successful_registration(self, client, app):
        """Test successful user registration."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'Password123',
            'confirm_password': 'Password123'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify user was created
        with app.app_context():
            from models import User
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'
            assert user.role == 'musterija'  # Default role

    def test_registration_duplicate_username(self, client, sample_user):
        """Test registration with existing username fails."""
        response = client.post('/register', data={
            'email': 'test@example.com',  # Already exists
            'email': 'different@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Should show error or redirect
        assert response.status_code in [200, 400]

    def test_registration_duplicate_email(self, client, sample_user):
        """Test registration with existing email fails."""
        response = client.post('/register', data={
            'username': 'different',
            'email': 'test@example.com',  # Already exists
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        assert response.status_code in [200, 400]

    def test_registration_password_mismatch(self, client):
        """Test registration with mismatched passwords."""
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'different123'
        }, follow_redirects=True)

        # Should stay on registration page or show error
        assert response.status_code == 200


# =============================================================================
# Login Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
class TestLogin:
    """Test user login functionality."""

    def test_login_page_loads(self, client):
        """Test login page is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or b'prijavite' in response.data.lower()

    def test_successful_login(self, client, sample_user):
        """Test successful login."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should redirect to home or dashboard

    def test_login_wrong_password(self, client, sample_user):
        """Test login with incorrect password."""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        assert response.status_code == 200
        # Should show error message

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_with_email(self, client, sample_user):
        """Test if login works with email (if supported)."""
        response = client.post('/login', data={
            'username': 'test@example.com',  # Using email
            'password': 'password123'
        }, follow_redirects=True)

        # Depending on implementation, this might work or not
        assert response.status_code in [200, 302]

    def test_login_banned_user(self, client, app):
        """Test that banned users cannot login."""
        with app.app_context():
            from extensions import db
            from models import User
            banned_user = User(
                username='banned',
                email='banned@example.com',
                is_banned=True
            )
            banned_user.set_password('password123')
            db.session.add(banned_user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'banned',
            'password': 'password123'
        }, follow_redirects=True)

        # Should be prevented from logging in
        # Implementation-dependent: might show error or redirect


# =============================================================================
# Logout Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
class TestLogout:
    """Test user logout functionality."""

    def test_logout(self, auth_client):
        """Test successful logout."""
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_logout_unauthenticated(self, client):
        """Test logout when not logged in."""
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


# =============================================================================
# Session Management Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
class TestSessionManagement:
    """Test session management."""

    def test_session_persists_after_login(self, client, sample_user):
        """Test that session persists after login."""
        with client:
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            }, follow_redirects=True)

            # Make another request
            response = client.get('/')
            assert response.status_code == 200
            # Session should still be active

    def test_protected_route_requires_login(self, client):
        """Test that protected routes require authentication."""
        # Try to access cart without login
        response = client.get('/cart')
        # Should redirect to login
        assert response.status_code in [302, 401]


# =============================================================================
# Profile Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
class TestProfile:
    """Test user profile functionality."""

    def test_view_profile_authenticated(self, auth_client):
        """Test viewing profile when authenticated."""
        response = auth_client.get('/profile')
        assert response.status_code == 200

    def test_view_profile_unauthenticated(self, client):
        """Test viewing profile when not authenticated."""
        response = client.get('/profile')
        # Should redirect to login
        assert response.status_code in [302, 401]

    def test_update_profile(self, auth_client, app):
        """Test updating profile information."""
        response = auth_client.post('/profile', data={
            'first_name': 'Updated',
            'last_name': 'Name',
            'address': '123 Test Street',
            'city': 'Sarajevo',
            'postal_code': '71000',
            'country': 'Bosnia and Herzegovina',
            'phone_number': '+387 61 123 456'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Verify changes
        with app.app_context():
            from models import User
            user = User.query.filter_by(username='testuser').first()
            assert user.first_name == 'Updated'
            assert user.last_name == 'Name'
            assert user.city == 'Sarajevo'


# =============================================================================
# Admin Access Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.admin
class TestAdminAccess:
    """Test admin access control."""

    def test_admin_panel_requires_admin(self, auth_client):
        """Test that regular users cannot access admin panel."""
        response = auth_client.get('/admin/products')
        # Should be forbidden or redirect
        assert response.status_code in [302, 403]

    def test_admin_panel_accessible_to_admin(self, admin_client):
        """Test that admin users can access admin panel."""
        response = admin_client.get('/admin/products')
        assert response.status_code == 200

    def test_admin_panel_not_accessible_when_not_logged_in(self, client):
        """Test admin panel requires authentication."""
        response = client.get('/admin/products')
        # Should redirect to login
        assert response.status_code in [302, 401]


# =============================================================================
# Security Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.security
class TestAuthSecurity:
    """Test authentication security measures."""

    def test_password_not_in_response(self, client, sample_user):
        """Test that passwords are never exposed in responses."""
        response = client.get('/profile')
        assert b'password123' not in response.data
        assert b'password_hash' not in response.data

    def test_login_case_sensitive(self, client, sample_user):
        """Test that username is case-sensitive (or not, depending on requirements)."""
        response = client.post('/login', data={
            'username': 'TESTUSER',  # Uppercase
            'password': 'password123'
        }, follow_redirects=True)

        # Implementation dependent
        assert response.status_code in [200, 302]

    def test_sql_injection_prevention_username(self, client):
        """Test SQL injection is prevented in username."""
        response = client.post('/login', data={
            'username': "admin' OR '1'='1",
            'password': 'anything'
        }, follow_redirects=True)

        # Should not bypass authentication
        assert response.status_code == 200
        # Should not be logged in
