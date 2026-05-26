"""
Environment Variable Validation Module

This module validates that all required environment variables are set
before the application starts, preventing runtime errors.
"""

import os
import sys


# Define required environment variables for each environment
REQUIRED_ENV_VARS = {
    'production': [
        'SESSION_SECRET',
        'STRIPE_SECRET_KEY',
        'DATABASE_URL'
    ],
    'development': [
        'SESSION_SECRET'  # Minimal requirements for dev
    ],
    'testing': []  # No requirements for testing (uses defaults)
}

# Define optional but recommended environment variables
RECOMMENDED_ENV_VARS = {
    'production': [
        'STRIPE_PUBLISHABLE_KEY',
        'MAIL_SERVER',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'SENTRY_DSN'  # Error tracking
    ],
    'development': [
        'STRIPE_SECRET_KEY'
    ],
    'testing': []
}


def validate_environment(config_name='development'):
    """
    Validate that all required environment variables are set.

    Args:
        config_name (str): Configuration name (development, testing, production)

    Raises:
        SystemExit: If required environment variables are missing in production
    """
    config_name = config_name.lower()

    # Get required variables for this environment
    required = REQUIRED_ENV_VARS.get(config_name, [])
    recommended = RECOMMENDED_ENV_VARS.get(config_name, [])

    # Check for missing required variables
    missing_required = [var for var in required if not os.environ.get(var)]
    missing_recommended = [var for var in recommended if not os.environ.get(var)]

    # Handle missing required variables
    if missing_required:
        print("\n" + "=" * 70)
        print("ERROR: Missing Required Environment Variables")
        print("=" * 70)
        print(f"Environment: {config_name}")
        print(f"Missing variables: {', '.join(missing_required)}")
        print("\nThese environment variables must be set before running the application.")
        print("Please create a .env file based on .env.example")
        print("=" * 70 + "\n")

        if config_name == 'production':
            # Fail hard in production
            sys.exit(1)
        else:
            # Warning in development
            print("WARNING: Continuing anyway (development mode)")
            print("Some features may not work correctly.\n")

    # Handle missing recommended variables
    if missing_recommended:
        print("\n" + "=" * 70)
        print(f"WARNING: Missing Recommended Environment Variables ({config_name})")
        print("=" * 70)
        print(f"Missing variables: {', '.join(missing_recommended)}")
        print("\nThese variables are recommended but not required.")
        print("Some features may be disabled or use default values.")
        print("=" * 70 + "\n")

    # Guard against running DEBUG mode with production database
    _check_debug_production_guard(config_name)

    # Validate specific variable formats
    _validate_variable_formats(config_name)

    # Success message
    if not missing_required and not missing_recommended:
        print(f"[OK] Environment variables validated successfully ({config_name})")


def _check_debug_production_guard(config_name):
    """
    Prevent running in debug/development mode with a production database.

    Args:
        config_name (str): Configuration name
    """
    if config_name in ('development', 'testing'):
        db_url = os.environ.get('DATABASE_URL', '')
        # If a non-SQLite database is configured in dev mode, warn loudly
        if db_url and not db_url.startswith('sqlite:///'):
            print("\n" + "=" * 70)
            print("WARNING: Non-SQLite database detected in development/testing mode!")
            print("=" * 70)
            print(f"DATABASE_URL points to: {db_url[:30]}...")
            print("Make sure you are NOT connecting to a production database.")
            print("Set FLASK_ENV=production if this is intentional.")
            print("=" * 70 + "\n")


def _validate_variable_formats(config_name):
    """
    Validate that environment variables have correct formats.

    Args:
        config_name (str): Configuration name
    """
    errors = []

    # Validate SESSION_SECRET length
    session_secret = os.environ.get('SESSION_SECRET', '')
    if session_secret and len(session_secret) < 16:
        errors.append("SESSION_SECRET should be at least 16 characters long")

    # Validate SESSION_SECRET is not default or weak in production
    if config_name == 'production':
        weak_secrets = ['dev-secret-key', 'your-secret-key-here-change-in-production', 'secret', 'password']
        if not session_secret:
            errors.append("SESSION_SECRET must be set in production (generate with: python -c \"import secrets; print(secrets.token_hex(32))\")")
        elif session_secret in weak_secrets:
            errors.append("SESSION_SECRET must be changed from default value in production")

    # Validate STRIPE_SECRET_KEY format
    stripe_key = os.environ.get('STRIPE_SECRET_KEY', '')
    if stripe_key:
        if config_name == 'production' and not stripe_key.startswith('sk_live_'):
            errors.append("STRIPE_SECRET_KEY should start with 'sk_live_' in production")
        elif config_name == 'development' and stripe_key.startswith('sk_live_'):
            errors.append("WARNING: Using live Stripe key in development!")

    # Validate DATABASE_URL format
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        valid_prefixes = ['sqlite:///', 'postgresql://', 'mysql://']
        if not any(db_url.startswith(prefix) for prefix in valid_prefixes):
            errors.append(f"DATABASE_URL should start with one of: {', '.join(valid_prefixes)}")

    # Print validation errors
    if errors:
        print("\n" + "=" * 70)
        print("Environment Variable Validation Warnings:")
        print("=" * 70)
        for error in errors:
            print(f"  • {error}")
        print("=" * 70 + "\n")


def get_env_var(key, default=None, required=False):
    """
    Get environment variable with optional default and requirement check.

    Args:
        key (str): Environment variable name
        default: Default value if not found
        required (bool): Whether this variable is required

    Returns:
        str: Environment variable value or default

    Raises:
        ValueError: If required variable is not found
    """
    value = os.environ.get(key, default)

    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")

    return value


def print_env_info():
    """Print information about current environment configuration."""
    flask_env = os.environ.get('FLASK_ENV', 'development')

    print("\n" + "=" * 70)
    print("Environment Configuration")
    print("=" * 70)
    print(f"FLASK_ENV: {flask_env}")
    print(f"DEBUG: {os.environ.get('DEBUG', 'not set')}")
    print(f"DATABASE_URL: {'set' if os.environ.get('DATABASE_URL') else 'not set (using default)'}")
    print(f"STRIPE_SECRET_KEY: {'set' if os.environ.get('STRIPE_SECRET_KEY') else 'not set'}")
    print(f"SESSION_SECRET: {'set' if os.environ.get('SESSION_SECRET') else 'not set'}")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    # Test the validator
    import sys
    env = sys.argv[1] if len(sys.argv) > 1 else 'development'
    validate_environment(env)
    print_env_info()
