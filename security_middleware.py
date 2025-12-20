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

    @app.after_request
    def set_security_headers(response):
        """Add security headers to every response."""

        # Prevent clickjacking - don't allow site to be framed
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS filter in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy - allows inline styles/scripts for now
        # TODO: Move to external CSS/JS files and tighten CSP
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
        response.headers['Content-Security-Policy'] = csp

        # Force HTTPS in production (only if not in development/testing)
        if not app.config.get('TESTING') and not app.debug:
            # HSTS: Force HTTPS for 1 year, include subdomains
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Set secure cookie flags
        if not app.config.get('TESTING'):
            # Ensure session cookies are secure
            app.config['SESSION_COOKIE_SECURE'] = not app.debug  # Only in production
            app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
            app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

            # Ensure remember me cookies are secure
            app.config['REMEMBER_COOKIE_SECURE'] = not app.debug
            app.config['REMEMBER_COOKIE_HTTPONLY'] = True
            app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

        return response

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
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

    # Prevent session fixation attacks
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    return app
