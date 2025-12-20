import os
from markupsafe import Markup, escape

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# Base configuration
class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "instance", "pcshop.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EUR_TO_BAM_RATE = 1.95583  # Fixed exchange rate for Bosnia and Herzegovina convertible mark
    MARKUP_PERCENTAGE = 15  # 15% markup on converted prices
    SHIPPING_COST = 10.0  # Dodajemo cijenu dostave

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.example.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-password')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@pcshop.com')

    # Component types for PC builder
    COMPONENT_TYPES = [
        'CPU', 'Motherboard', 'RAM', 'GPU', 'Storage', 'Power Supply',
        'CPU Cooler', 'Case', 'Case Fans', 'Monitor', 'Keyboard', 'Mouse'
    ]

    # Product categories
    PRODUCT_CATEGORIES = [
        'CPUs', 'Motherboards', 'Memory', 'Graphics Cards', 'Storage',
        'Power Supplies', 'Cases', 'Cooling', 'Peripherals', 'Monitors',
        'Networking', 'Software'
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    RATELIMIT_ENABLED = False  # Disable rate limiting for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF for tests


class ProductionConfig(Config):
    pass


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
