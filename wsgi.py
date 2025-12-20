#!/usr/bin/env python3
"""
WSGI entry point for Sajborg.com Flask application
"""
import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, '/var/www/Sajborg')

# Set environment to production
os.environ['FLASK_ENV'] = 'production'

from app import create_app

# Create the application instance
application = create_app('production')

if __name__ == "__main__":
    application.run()
