# Sajborg.com - E-Commerce Platform

A modern, full-featured e-commerce platform for computer components built with Flask. Features include user authentication, product catalog, shopping cart, Stripe payments, PC Builder tool, blog system, and admin dashboard.

## Features

- **User Accounts** - Registration, login, profiles with order history
- **Product Catalog** - Search, filtering, categories, detailed specifications
- **Shopping Cart** - Item management, extended warranty options
- **Order Management** - Checkout process, order tracking, admin panel
- **PC Builder** - Interactive tool for building custom PC configurations
- **Blog System** - CMS with rich text editor
- **Real-time Chat** - Communication between users and administrators
- **Admin Dashboard** - Complete store management interface
- **Security** - Rate limiting, CSRF protection, secure file uploads, bcrypt password hashing

## Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Flask 3.0, Python 3 |
| **Database** | SQLite (dev), PostgreSQL (production) |
| **ORM** | SQLAlchemy 2.0 |
| **Frontend** | Bootstrap 5, Jinja2 Templates |
| **Authentication** | Flask-Login, Flask-Bcrypt |
| **Payments** | Stripe API |
| **Testing** | Pytest (126 tests) |
| **Security** | Flask-Limiter, Flask-WTF (CSRF), Bleach |

## Installation

### Prerequisites

- Python 3.8+
- pip
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sajborg.com.git
   cd sajborg.com
   ```

2. **Create and activate virtual environment**
   ```bash
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///instance/pcshop.db
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   FLASK_ENV=development
   ```

5. **Initialize the database**
   ```bash
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   flask run
   ```

   The application will be available at `http://localhost:5000`

## Project Structure

```
sajborg.com/
├── app.py              # Flask application factory
├── config.py           # Configuration classes
├── models.py           # SQLAlchemy database models
├── extensions.py       # Flask extension initialization
├── wsgi.py             # Production WSGI entry point
│
├── routes/             # Flask blueprints
│   ├── auth.py         # Authentication routes
│   ├── main.py         # Homepage and main routes
│   ├── product.py      # Product listing and details
│   ├── cart.py         # Shopping cart
│   ├── pc_builder.py   # PC Builder tool
│   ├── blog_routes.py  # Blog system
│   └── admin/          # Admin panel routes
│
├── forms/              # WTForms form classes
├── templates/          # Jinja2 HTML templates
├── static/             # CSS, JS, images
├── migrations/         # Database migrations (Alembic)
├── tests/              # Pytest test suite
└── dokumentacija/      # Project documentation
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage report:
```bash
pytest tests/ --cov=. --cov-report=html
```

View coverage report in `htmlcov/index.html`

### Test Categories

Tests are organized with markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.cart` - Shopping cart tests
- `@pytest.mark.admin` - Admin panel tests
- `@pytest.mark.security` - Security tests

## Configuration

The application supports multiple environments:

| Environment | Config Class | Database |
|-------------|--------------|----------|
| Development | `DevelopmentConfig` | SQLite |
| Testing | `TestingConfig` | SQLite (in-memory) |
| Production | `ProductionConfig` | PostgreSQL |

Set the environment via `FLASK_ENV` in your `.env` file.

## Deployment

### Using the Deployment Script (Ubuntu/Linux)

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

This script will:
- Create virtual environment
- Install dependencies
- Configure Nginx
- Set up SSL with Certbot
- Configure Gunicorn
- Create systemd service

### Manual Deployment with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Products
- `GET /shop` - Product listing
- `GET /shop/product/<id>` - Product details
- `GET /shop/category/<slug>` - Category products

### Cart
- `POST /cart/add/<product_id>` - Add to cart
- `POST /cart/update/<item_id>` - Update quantity
- `POST /cart/remove/<item_id>` - Remove item
- `GET /cart/checkout` - Checkout page

### Admin (requires admin role)
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/products` - Product management
- `GET /admin/orders` - Order management
- `GET /admin/users` - User management

## Security Features

- **Password Hashing** - Bcrypt with secure salt
- **CSRF Protection** - Flask-WTF token validation
- **Rate Limiting** - 200 requests/day, 50 requests/hour
- **Input Sanitization** - Bleach HTML sanitizer
- **SQL Injection Prevention** - SQLAlchemy ORM
- **Secure Headers** - Security middleware
- **File Upload Validation** - Type and size restrictions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

Additional documentation is available in the `dokumentacija/` folder:

- `CODEBASE_DOCUMENTATION.md` - Architecture overview
- `SECURITY_HARDENING_COMPLETED.md` - Security implementation
- `PERFORMANCE_OPTIMIZATION_SUMMARY.md` - Performance optimizations
- `TESTING_GUIDE.md` - Testing procedures
- `MOBILE_RESPONSIVENESS.md` - Mobile UI support

## License

Copyright (c) 2025 Sajborg Shop. All Rights Reserved. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - Frontend framework
- [Stripe](https://stripe.com/) - Payment processing
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
