import os
import logging
import json
from datetime import timedelta
import time # NOVI IMPORT
import bleach

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from markupsafe import Markup, escape
from config import config
from extensions import db, init_extensions, login_manager
from models import Category  # Import the Category model
from env_validator import validate_environment  # Environment validation
from security import configure_security  # Security headers and utilities
from security_middleware import add_security_headers, configure_security_settings  # NEW: Security middleware

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def create_app(config_name='default'):
    # Validate environment variables before creating app
    validate_environment(config_name)

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Session and security configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),

        # CSRF Configuration
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=app.secret_key,
        WTF_CSRF_TIME_LIMIT=None,  # No time limit for CSRF tokens
        WTF_CSRF_SSL_STRICT=False,  # Allow CSRF tokens on http for development
        WTF_CSRF_CHECK_DEFAULT=True,
        WTF_CSRF_METHODS=['POST', 'PUT', 'PATCH', 'DELETE']
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure the database if not set in config
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/pcshop.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Add custom filters
    @app.template_filter('json_loads')
    def json_loads_filter(s):
        return json.loads(s) if s else {}

    @app.template_filter('nl2br')
    def nl2br(value):
        return Markup('<br>\n').join(escape(value).split('\n'))

    @app.template_filter('bool_to_da_ne')
    def bool_to_da_ne(value):
        """Convert boolean or string boolean values to Da/Ne"""
        if isinstance(value, bool):
            return 'Da' if value else 'Ne'
        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes', 'da']:
                return 'Da'
            elif value.lower() in ['false', '0', 'no', 'ne']:
                return 'Ne'
        return value

    @app.template_filter('sanitize_html')
    def sanitize_html(value):
        """Sanitize HTML content to prevent XSS attacks"""
        if not value:
            return ''

        # Allowed HTML tags for blog posts
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre',
            'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'div', 'span'
        ]

        # Allowed attributes for specific tags
        allowed_attrs = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'div': ['class'],
            'span': ['class'],
            'code': ['class'],
            'pre': ['class']
        }

        # Sanitize the HTML
        clean_html = bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )

        return Markup(clean_html)

    # Context processors to make variables available to all templates
    @app.context_processor
    def inject_global_vars():
        # IZMJENA OVDJE: Dodajemo filter_by(is_public=True)
        all_categories = Category.query.filter_by(parent_id=None, is_public=True).order_by(Category.name).all()
        return dict(
            all_categories=all_categories,
            timedelta=timedelta,
            cache_buster=int(time.time()) # NOVI RED za cache busting
        )

    # Initialize extensions
    init_extensions(app)

    # Configure security headers and utilities
    configure_security(app)

    # Add security headers middleware (NEW)
    add_security_headers(app)
    configure_security_settings(app)

    with app.app_context():
        # Import models and create tables
        import models
        db.create_all()

        # User loader callback
        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

        # Register blueprints
        from routes.auth import auth_bp
        from routes.main import main_bp
        from routes.product import product_bp
        from routes.interaction import interaction_bp
        from routes.admin import admin_bp
        from routes.cart import cart_bp
        from routes.pc_builder import builder_bp
        from routes.lager import lager_bp
        from routes.seo_routes import seo_bp
        from routes.chat import chat_bp
        from routes.blog_routes import blog_bp # NOVI IMPORT

        app.register_blueprint(seo_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(product_bp)
        app.register_blueprint(interaction_bp)
        app.register_blueprint(admin_bp)
        app.register_blueprint(cart_bp)
        app.register_blueprint(builder_bp)
        app.register_blueprint(lager_bp)
        app.register_blueprint(chat_bp)
        app.register_blueprint(blog_bp) # REGISTRACIJA NOVOG BLUEPRINTA

        # Error handlers
        @app.errorhandler(403)
        def forbidden(e):
            from flask import render_template
            return render_template('errors/403.html'), 403

        @app.errorhandler(404)
        def page_not_found(e):
            from flask import render_template
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_server_error(e):
            from flask import render_template
            return render_template('errors/500.html'), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)