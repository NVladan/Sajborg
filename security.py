"""
Security headers and middleware.

This module provides security headers and utilities to protect
the application against common web vulnerabilities.
"""

from flask import make_response, request


def add_security_headers(response):
    """
    Add security headers to all HTTP responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable browser XSS protection
    - Strict-Transport-Security: Force HTTPS (production)
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features

    Args:
        response: Flask response object

    Returns:
        Modified response object with security headers
    """
    # Prevent MIME type sniffing
    # Browsers won't try to guess content type
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Prevent clickjacking attacks
    # Page can only be displayed in a frame on the same origin
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # Enable browser's built-in XSS protection
    # Note: Modern browsers have this by default, but doesn't hurt
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Force HTTPS connections (only in production)
    # max-age: 1 year in seconds
    # includeSubDomains: Apply to all subdomains
    # Note: Only enable this when you have HTTPS set up!
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    # Restricts what resources can be loaded
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "  # Default: only load from same origin
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://cdn.jsdelivr.net; "  # Scripts
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "  # Styles
        "img-src 'self' data: https: blob:; "  # Images (allow https and data URLs)
        "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "  # Fonts
        "connect-src 'self' https://api.stripe.com; "  # AJAX/fetch
        "frame-src 'self' https://js.stripe.com; "  # iframes (Stripe)
        "object-src 'none'; "  # No Flash/Java applets
        "base-uri 'self'; "  # Restrict <base> tag
        "form-action 'self'; "  # Forms can only submit to same origin
        "upgrade-insecure-requests"  # Upgrade HTTP to HTTPS
    )

    # Control how much referrer information is shared
    # strict-origin-when-cross-origin: Send full URL for same-origin,
    # only origin for cross-origin, nothing on HTTPS -> HTTP downgrade
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Control which browser features can be used
    # Disable potentially dangerous features
    response.headers['Permissions-Policy'] = (
        "geolocation=(), "  # No geolocation
        "microphone=(), "  # No microphone
        "camera=(), "  # No camera
        "payment=(self), "  # Payment only for same origin (Stripe)
        "usb=(), "  # No USB
        "magnetometer=(), "  # No magnetometer
        "accelerometer=(), "  # No accelerometer
        "gyroscope=()"  # No gyroscope
    )

    return response


def configure_security(app):
    """
    Configure all security features for the application.

    This function should be called during application initialization.

    Args:
        app: Flask application instance
    """
    # Add security headers to all responses
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)

    # Add Content-Disposition header for uploaded files to prevent stored XSS
    @app.after_request
    def add_content_disposition(response):
        if response.content_type and response.content_type.startswith('image/'):
            if '/uploads/' in (request.path or ''):
                response.headers['Content-Disposition'] = 'inline'
                response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    # Optionally: Add security logging
    @app.after_request
    def log_security_events(response):
        # Log suspicious activities
        # This is a placeholder - implement based on your needs
        return response


def create_rate_limit_error_response():
    """
    Create a custom response for rate limit errors.

    Returns:
        Tuple of (response_content, status_code, headers)
    """
    return (
        {
            'error': 'Rate limit exceeded',
            'message': 'Previše zahteva. Molimo pokušajte kasnije.',
            'status': 429
        },
        429,
        {'Content-Type': 'application/json', 'Retry-After': '60'}
    )


# Security utility functions

def is_safe_url(target, request):
    """
    Check if a redirect URL is safe (prevents open redirect attacks).

    Args:
        target: URL to redirect to
        request: Flask request object

    Returns:
        bool: True if URL is safe, False otherwise
    """
    from urllib.parse import urlparse, urljoin
    from flask import request as flask_request

    ref_url = urlparse(flask_request.host_url)
    test_url = urlparse(urljoin(flask_request.host_url, target))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def sanitize_html_input(text):
    """
    Sanitize HTML input to prevent XSS attacks.

    Note: Jinja2 auto-escapes by default, but this is for
    additional protection when needed.

    Args:
        text: Input text to sanitize

    Returns:
        Sanitized text with HTML entities escaped
    """
    from markupsafe import escape
    return escape(text)


def generate_csrf_token():
    """
    Generate a CSRF token for forms.

    Returns:
        CSRF token string
    """
    from flask_wtf.csrf import generate_csrf
    return generate_csrf()
