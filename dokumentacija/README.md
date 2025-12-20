# PC Parts Shop

A comprehensive Flask-based e-commerce website for PC parts and electronics, featuring responsive design, multiple payment options (Stripe and Cash on Delivery), PC builder functionality, and an admin panel.

## Features

- **User Authentication**: Register, login, and profile management
- **Product Browsing**: Browse products by categories with search and filter options
- **Shopping Cart**: Add products to cart, update quantities, and remove items
- **Checkout Process**: Secure checkout with multiple payment options
- **PC Builder Tool**: Build custom PC configurations with compatibility checking
- **Admin Panel**: Manage products, categories, and orders
- **Responsive Design**: Mobile-friendly UI using Bootstrap

## Setup Guide

### 1. Environment Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd pc-parts-shop
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r dependencies.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory with the following variables:
   ```
   STRIPE_SECRET_KEY=your_stripe_secret_key
   SESSION_SECRET=your_session_secret
   ```

### 2. Database Setup

1. **Run the application** to create the SQLite database and tables:
   ```bash
   python main.py
   ```

   This will create a `pcshop.db` SQLite database file in the root directory.

### 3. Adding Sample Data

1. **Add sample products**:
   ```bash
   python add_samples.py
   ```

   This will create sample categories and products for testing the shop functionality.

### 4. Data Scraping from ipon.hu

The project includes a scraper for importing product data from ipon.hu. To use it:

1. **Run the scraper script**:
   ```bash
   # Create a python file with the following content
   # scrape_run.py
   from scrapers import scrape_ipon_products

   if __name__ == "__main__":
       scrape_ipon_products()

   # Then run it
   python scrape_run.py
   ```

This will scrape product data from various categories and import them into the database with prices converted to BAM currency with a markup.

## Admin Access

To access the admin panel:

1. **Create an admin user** through the Flask shell:
   ```bash
   flask shell
   ```

   In the shell:
   ```python
   from app import db
   from models import User

   # Create a new admin user
   admin = User()
   admin.username = "admin"
   admin.email = "admin@example.com"
   admin.set_password("your_password")
   admin.is_admin = True
   db.session.add(admin)
   db.session.commit()
   ```

2. **Access the admin panel**:
   Login with the admin credentials, then navigate to `/admin/dashboard` or click on "Admin Dashboard" in the user dropdown menu.

## Payment System

The application supports two payment methods:

1. **Stripe Payment**: Processes card payments through Stripe's checkout system. Requires a valid Stripe API key.
2. **Cash on Delivery**: Allows customers to place orders and pay upon delivery.

## Project Structure

- **app.py**: Main Flask application setup
- **main.py**: Entry point for running the application
- **models.py**: Database models for the application
- **config.py**: Configuration settings
- **forms.py**: Form classes for data validation
- **utils.py**: Utility functions used across the application
- **routes/**: Route handlers organized by feature
- **templates/**: Jinja2 templates for rendering HTML
- **static/**: Static assets (CSS, JavaScript, images)
- **scrapers/**: Data scraping functionality

## Running the Application

```bash
python main.py
```

The application will be accessible at http://localhost:5000

## Testing

The project includes a comprehensive test suite in the `/tests` directory. 

### Installing Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Running Tests

```bash
pytest
```

For test coverage report:

```bash
pytest --cov=.
```

For more detailed information about the tests and how to run specific tests, see the [tests/README.md](tests/README.md) file.

## Deployment

For production deployment, use a production WSGI server like Gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

## Dependencies

Major dependencies include:

- Flask: Web framework
- SQLAlchemy: ORM for database operations
- Flask-Login: User authentication
- Flask-WTF: Form handling and validation
- Stripe: Payment processing
- Trafilatura: Web scraping
- Pandas: Data processing

See `dependencies.txt` for a complete list.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
