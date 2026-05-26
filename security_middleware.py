"""
Security middleware for adding HTTP security headers.

This module provides middleware to add security headers to all responses,
protecting against common web vulnerabilities.
"""

from flask import Flask


def add_security_headers(app: Flask):
    """
    Add security headers middleware to Flask app.

    Headers added:
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-XSS-Protection: Enables XSS filter in browsers
    - Strict-Transport-Security: Forces HTTPS (production only)
    - Content-Security-Policy: Prevents XSS and injection attacks
    - Referrer-Policy: Controls referrer information
    """

    # Security headers are handled by security.py (configure_security).
    # This module only handles cookie flags and HSTS to avoid duplicate headers.

    @app.after_request
    def set_cookie_security(response):
        """Set secure cookie flags and HSTS (headers set by security.py)."""

        # Force HTTPS in production (only if not in development/testing)
        if not app.config.get('TESTING') and not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    # Set cookie flags once at init, not on every request
    if not app.config.get('TESTING'):
        app.config['SESSION_COOKIE_SECURE'] = not app.debug
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['REMEMBER_COOKIE_SECURE'] = not app.debug
        app.config['REMEMBER_COOKIE_HTTPONLY'] = True
        app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

    return app


def configure_security_settings(app: Flask):
    """
    Configure additional security settings for the Flask app.

    Args:
        app: Flask application instance
    """
    # Limit maximum content length to prevent DOS attacks (16MB)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Set secure session configuration
    app.config['SESSION_COOKIE_NAME'] = 'sajborg_session'
    # PERMANENT_SESSION_LIFETIME is set in app.py (7 days) - do not override here

    # Prevent session fixation attacks
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    return app
