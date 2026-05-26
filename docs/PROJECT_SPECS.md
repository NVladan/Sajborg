# Sajborg.com - Complete Project Specification

> Full-featured e-commerce platform for computer components, built with Flask.
> Includes a PC builder tool, warehouse management, real-time chat, blog/tech magazine, and a comprehensive admin panel.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Architecture](#4-architecture)
5. [Database Schema](#5-database-schema)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Routes & Endpoints](#7-routes--endpoints)
8. [Business Logic & Flows](#8-business-logic--flows)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Admin Panel](#10-admin-panel)
11. [Security](#11-security)
12. [Configuration & Environment](#12-configuration--environment)
13. [Deployment](#13-deployment)
14. [Testing](#14-testing)
15. [Third-Party Integrations](#15-third-party-integrations)

---

## 1. Overview

**Sajborg.com** is a production-ready e-commerce platform specializing in computer hardware and components. The platform serves the Bosnian market with prices in BAM (Convertible Mark), converted from EUR with configurable markup.

### Core Capabilities

- **Product Catalog** - Hierarchical categories, dynamic attributes per category, multi-image galleries, search with autocomplete, advanced filtering and sorting
- **Shopping Cart & Checkout** - Session-based cart with extended warranty options, cash-on-delivery checkout, order lifecycle management
- **PC Builder** - Interactive tool for assembling custom PC configurations with real-time compatibility checking (CPU socket, RAM type, PSU wattage)
- **Warehouse (Lager)** - Internal inventory management system with role-gated access for distributors and suppliers
- **Real-time Chat** - Customer-to-admin messaging system with read/unread tracking
- **Blog / Tech Magazine** - Content management with rich text editing, featured images, and publish controls
- **Admin Panel** - Full CRUD for products, categories, orders, users, blog posts, and bulk import

### Target Market

- **Region**: Bosnia and Herzegovina
- **Currency**: BAM (Konvertibilna Marka) with EUR-to-BAM conversion
- **Language**: Bosnian (UI labels, form validation messages, flash messages)
- **Domain**: sajborg.com

---

## 2. Tech Stack

### Backend

| Component | Technology | Version |
|---|---|---|
| Framework | Flask | 3.0.3 |
| ORM | Flask-SQLAlchemy / SQLAlchemy | 3.1.1 / 2.0.31 |
| Auth | Flask-Login | 0.6.3 |
| Forms & CSRF | Flask-WTF | 1.2.1 |
| Migrations | Flask-Migrate / Alembic | 4.0.7 / 1.13.2 |
| Password Hashing | Werkzeug (generate_password_hash) | 3.0.3 |
| Rate Limiting | Flask-Limiter | 3.5.0 |
| HTML Sanitization | Bleach | 6.3.0 |
| Image Processing | Pillow | 10.2.0 |
| Data Import | pandas + openpyxl | 2.1.4 / 3.1.2 |
| URL Slugs | python-slugify | latest |
| Env Management | python-dotenv | 1.0.1 |
| Payment (prepared) | Stripe | 10.2.0 |

### Frontend

| Component | Technology |
|---|---|
| Template Engine | Jinja2 3.1.4 |
| CSS Framework | Bootstrap (via Flask-Bootstrap 3.3.7.1) |
| JavaScript | Vanilla JS + jQuery (CDN) |
| Icons | FontAwesome 6+ (local vendor) |
| Rich Text Editor | Summernote (for blog admin) |

### Database

| Environment | Database |
|---|---|
| Development | SQLite (`instance/pcshop.db`) |
| Testing | SQLite (in-memory / `test.db`) |
| Production | PostgreSQL (recommended), MySQL (supported) |

### Production Stack

| Component | Technology |
|---|---|
| WSGI Server | Gunicorn (4 workers, Unix socket) |
| Reverse Proxy | Nginx |
| Process Manager | systemd |
| SSL | Let's Encrypt / Certbot |
| OS | Ubuntu (targeted by deploy script) |

---

## 3. Project Structure

```
Sajborg.com/
|
|-- app.py                        # App factory: create_app(), template filters, context processors,
|                                 #   blueprint registration, error handlers
|-- config.py                     # Config classes (Dev, Test, Production) + business constants
|-- extensions.py                 # Extension initialization (db, login_manager, csrf, limiter, migrate)
|-- models.py                     # All SQLAlchemy models (14 models, 17 tables)
|-- utils.py                      # Business logic utilities (pricing, compatibility, file validation)
|-- security.py                   # Security headers, CSP, HSTS, safe URL check, CSRF helpers
|-- security_middleware.py        # Additional security middleware (headers, cookie flags, content limits)
|-- env_validator.py              # Environment variable validation per config environment
|-- wsgi.py                       # Production WSGI entry point for Gunicorn
|-- requirements.txt              # Python dependencies (pinned versions)
|-- .env.example                  # Environment variable template
|-- deploy.sh                     # Automated deployment script for Ubuntu
|-- sajborg.service               # systemd unit file for Gunicorn
|-- nginx_sajborg.conf            # Nginx reverse proxy configuration
|
|-- routes/                       # Flask Blueprints (all route handlers)
|   |-- main.py                   # Homepage, about, privacy, terms
|   |-- auth.py                   # Login, register, logout, profile
|   |-- product.py                # Product listing, detail, reviews
|   |-- cart.py                   # Cart view, checkout, order creation
|   |-- pc_builder.py             # PC builder: component selection, compatibility, save/load
|   |-- interaction.py            # AJAX endpoints: add-to-cart, search suggestions, newsletter
|   |-- chat.py                   # Real-time chat between users and admin
|   |-- lager.py                  # Warehouse/inventory management
|   |-- seo_routes.py             # sitemap.xml, robots.txt generation
|   |-- blog_routes.py            # Blog/tech magazine frontend display
|   |-- admin/                    # Admin panel blueprint
|       |-- __init__.py           # Admin blueprint setup + @admin_required decorator
|       |-- dashboard.py          # Dashboard with stats and recent orders
|       |-- product_routes.py     # Product CRUD + attribute management
|       |-- category_routes.py    # Category CRUD + attribute schema definition
|       |-- product_image_routes.py # Multi-image upload, primary selection, reordering
|       |-- order_routes.py       # Order listing, detail, status transitions
|       |-- user_routes.py        # User management, role changes, ban/unban
|       |-- blog_routes.py        # Blog post CRUD (admin side)
|       |-- product_import_routes.py # Bulk CSV/Excel import
|
|-- forms/                        # WTForms form classes
|   |-- auth_forms.py             # LoginForm, RegistrationForm, ProfileForm
|   |-- product_forms.py          # ProductForm, CategoryForm, ImportForm
|   |-- checkout_forms.py         # CheckoutForm (shipping + payment info)
|   |-- builder_forms.py          # PC builder component selection forms
|   |-- review_forms.py           # ReviewForm (rating + text)
|
|-- templates/                    # Jinja2 HTML templates
|   |-- base.html                 # Master layout (navbar, footer, flash messages, global JS/CSS)
|   |-- auth/                     # login.html, register.html, profile.html
|   |-- shop/                     # products.html, product_detail.html, cart.html, checkout.html
|   |-- admin/                    # dashboard.html, product forms, order views, user management
|   |-- pc_builder/               # builder.html, build_detail.html
|   |-- blog/                     # blog_list.html, blog_post.html
|   |-- errors/                   # 403.html, 404.html, 500.html
|
|-- static/                       # Static assets
|   |-- css/                      # Stylesheets
|   |-- js/                       # JavaScript modules
|   |   |-- main.js               # Global utilities, search bar behavior
|   |   |-- cart.js               # Cart AJAX operations (quantity update, remove)
|   |   |-- pc_builder.js         # Builder UI logic, compatibility checks
|   |   |-- product_detail.js     # Product page: image gallery, review form
|   |   |-- admin.js              # Admin panel form validation, bulk actions
|   |   |-- chat.js               # Chat widget behavior, message polling
|   |   |-- modal_utils.js        # Reusable modal dialog functions
|   |-- img/                      # Static images and icons
|   |-- sounds/                   # Audio files
|   |-- uploads/                  # User-uploaded content
|   |   |-- products/             # Product images (organized by product ID)
|   |   |-- categories/           # Category banner images
|   |   |-- posts/                # Blog featured images
|   |-- vendor/                   # Vendored third-party assets (FontAwesome, jQuery)
|
|-- migrations/                   # Alembic database migration scripts
|-- tests/                        # Pytest test suite (126 tests)
|-- instance/                     # Instance-specific files (SQLite DB, not in version control)
|-- dokumentacija/                # Additional project documentation
|-- docs/                         # Technical specifications (this file)
```

---

## 4. Architecture

### 4.1 Application Pattern

The application follows the **Flask Application Factory** pattern:

```
create_app(config_name) -> Flask app
    1. Validate environment variables (env_validator.py)
    2. Load configuration class from config.py
    3. Configure session & CSRF settings
    4. Apply ProxyFix middleware (for Nginx)
    5. Register Jinja2 template filters (json_loads, nl2br, bool_to_da_ne, sanitize_html)
    6. Register context processor (global categories for navbar, cache_buster)
    7. Initialize extensions (db, migrate, login_manager, csrf, limiter)
    8. Configure security headers (security.py + security_middleware.py)
    9. Create all database tables (db.create_all)
    10. Register all 11 blueprints
    11. Register error handlers (403, 404, 500)
```

### 4.2 Blueprint Architecture

Each major feature area is isolated into its own Flask Blueprint:

| Blueprint | URL Prefix | Module |
|---|---|---|
| `main_bp` | `/` | `routes/main.py` |
| `auth_bp` | `/` | `routes/auth.py` |
| `product_bp` | `/` | `routes/product.py` |
| `cart_bp` | `/` | `routes/cart.py` |
| `builder_bp` | `/pc-builder` | `routes/pc_builder.py` |
| `interaction_bp` | `/interaction` | `routes/interaction.py` |
| `chat_bp` | `/chat` | `routes/chat.py` |
| `lager_bp` | `/lager` | `routes/lager.py` |
| `seo_bp` | `/` | `routes/seo_routes.py` |
| `blog_bp` | `/tech-magazin` | `routes/blog_routes.py` |
| `admin_bp` | `/admin` | `routes/admin/` |

### 4.3 Extension Initialization

All Flask extensions are instantiated in `extensions.py` and initialized with the app in `init_extensions(app)`:

- **SQLAlchemy** (`db`) - ORM with DeclarativeBase
- **Migrate** (`migrate`) - Database migration management
- **LoginManager** (`login_manager`) - Session-based auth, redirects to `auth.login`
- **CSRFProtect** (`csrf`) - CSRF token validation on POST/PUT/PATCH/DELETE
- **Limiter** (`limiter`) - Rate limiting with in-memory storage, fixed-window strategy

### 4.4 Request Lifecycle

```
Client Request
  |
  v
Nginx (static files, SSL, proxy headers)
  |
  v
Gunicorn (WSGI, 4 workers, Unix socket)
  |
  v
ProxyFix Middleware (X-Forwarded-For, X-Forwarded-Proto)
  |
  v
Flask App
  |-- Rate Limiter check
  |-- Session loading (Flask-Login)
  |-- CSRF token validation (POST/PUT/PATCH/DELETE)
  |-- Blueprint route handler
  |-- Template rendering (Jinja2 with global context)
  |-- Security headers added (@app.after_request)
  |
  v
Response to Client
```

---

## 5. Database Schema

### 5.1 Entity-Relationship Overview

```
User (1)----(N) Order
User (1)----(N) CartItem
User (1)----(N) PCBuild
User (1)----(N) Review
User (1)----(N) Message (sent)
User (1)----(N) Message (received)
User (1)----(N) Post

Category (1)----(N) Product
Category (1)----(N) Category (self-referential: parent/subcategories)
Category (1)----(N) CategoryAttribute

CategoryAttribute (1)----(N) AttributeOption
CategoryAttribute (1)----(N) ProductAttributeValue

Product (1)----(N) ProductImage
Product (1)----(N) ProductAttributeValue
Product (1)----(N) CartItem
Product (1)----(N) Review
Product (M)----(N) Order        (via order_items junction)
Product (M)----(N) PCBuild      (via build_components junction)

LagerCategory (1)----(N) LagerProduct
LagerCategory (1)----(N) LagerCategory (self-referential)
```

### 5.2 Model Definitions

#### User

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | Auto-increment identifier |
| username | String(64) | Unique, Not Null | Display name |
| email | String(120) | Unique, Not Null | Login email |
| password_hash | String(256) | Not Null | Werkzeug password hash |
| first_name | String(64) | Nullable | Shipping info |
| last_name | String(64) | Nullable | Shipping info |
| address | String(256) | Nullable | Shipping info |
| city | String(64) | Nullable | Shipping info |
| postal_code | String(32) | Nullable | Shipping info |
| country | String(64) | Nullable | Shipping info |
| phone_number | String(32) | Nullable | Contact info |
| role | String(20) | Not Null, Default: `musterija` | One of: musterija, distributer, dobavljac, admin |
| is_subscribed | Boolean | Default: False | Newsletter subscription |
| is_banned | Boolean | Default: False, Not Null | Login block flag |
| created_at | DateTime | Default: utcnow | Registration timestamp |

#### Category

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| name | String(64) | Not Null | Display name |
| slug | String(64) | Unique, Not Null | URL-safe identifier |
| description | Text | Nullable | Category description |
| image_path | String(256) | Default: `img/category-default.png` | Banner image |
| parent_id | Integer | FK(category.id), Nullable | Self-referential for hierarchy |
| is_featured | Boolean | Default: False | Homepage display flag |
| component_type | String(64) | Nullable | PC builder mapping (CPU, GPU, etc.) |
| is_public | Boolean | Default: True, Not Null | Storefront visibility |

**Indexes**: `idx_category_parent`, `idx_category_featured`, `idx_category_public`

#### Product

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| name | String(128) | Not Null | Product title |
| slug | String(128) | Unique, Not Null | URL-safe identifier |
| description | Text | Nullable | Full description |
| price | Float | Not Null | Retail price in BAM |
| stock | Integer | Default: 0 | Available quantity |
| specs | Text | Nullable | Legacy JSON specs field |
| category_id | Integer | FK(category.id), Not Null | Parent category |
| component_type | String(64) | Nullable | PC builder component type |
| condition | String(20) | Not Null, Default: `Novo` | `Novo` (new) or `Polovno` (used) |
| availability | String(50) | Not Null, Default: `Dostupno odmah` | Availability status text |
| featured | Boolean | Default: False | Homepage featured flag |
| is_publicly_visible | Boolean | Default: True, Not Null | Storefront visibility |
| purchase_price | Float | Nullable | Internal cost price |
| reservation_note | String(255) | Nullable | Internal reservation info |
| internal_note | Text | Nullable | Internal admin notes |
| for_company | Boolean | Default: False | B2B product flag |
| created_at | DateTime | Default: utcnow | |
| updated_at | DateTime | Default: utcnow, onupdate: utcnow | |

**Indexes**: `idx_product_category_stock`, `idx_product_visibility`, `idx_product_featured`, `idx_product_component_type`

**Computed Property**: `average_rating` - mean of all associated review ratings

#### ProductImage

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| product_id | Integer | FK(product.id), Not Null | Parent product |
| image_path | String(256) | Not Null | File path relative to static/uploads |
| is_primary | Boolean | Default: False | Main product image flag |
| sort_order | Integer | Default: 0 | Display order |
| created_at | DateTime | Default: utcnow | |

#### CategoryAttribute (Dynamic Attribute Schema)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| category_id | Integer | FK(category.id), Not Null | Owning category |
| name | String(64) | Not Null | Attribute name (e.g., "Socket", "RAM", "TDP (W)") |
| type | String(32) | Default: `string` | Data type: string, int, float, bool, select |
| sort_order | Integer | Default: 0 | Display order in forms |

#### AttributeOption (Predefined values for `select` type attributes)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| attribute_id | Integer | FK(category_attribute.id), Not Null | Parent attribute |
| value | String(128) | Not Null | Option value |

#### ProductAttributeValue (Product-specific attribute values)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| product_id | Integer | FK(product.id), Not Null | |
| attribute_id | Integer | FK(category_attribute.id), Not Null | |
| value | String(128) | Not Null | Stored value |

**Indexes**: `idx_pav_product_attribute`, `idx_pav_attribute_value`

#### CartItem

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | FK(user.id), Not Null | Cart owner |
| product_id | Integer | FK(product.id), Not Null | |
| quantity | Integer | Default: 1 | |
| extended_warranty | Boolean | Default: False | +10% warranty option |
| added_at | DateTime | Default: utcnow | |

**Index**: `idx_cartitem_user_product`

#### Order

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | FK(user.id), Not Null | |
| total_amount | Float | Not Null | Order total in BAM |
| status | String(32) | Default: `pending` | Lifecycle state |
| payment_method | String(32) | Default: `cash_on_delivery` | |
| shipping_first_name | String(64) | Nullable | Snapshot of shipping address |
| shipping_last_name | String(64) | Nullable | |
| shipping_address | String(256) | Nullable | |
| shipping_city | String(64) | Nullable | |
| shipping_postal_code | String(32) | Nullable | |
| shipping_country | String(64) | Nullable | |
| shipping_phone_number | String(32) | Nullable | |
| created_at | DateTime | Default: utcnow | |
| updated_at | DateTime | Default: utcnow, onupdate: utcnow | |

**Indexes**: `idx_order_user_status`, `idx_order_status_created`

**Computed Property**: `full_shipping_address` - formatted multi-line address string

#### order_items (Junction Table)

| Column | Type | Constraints | Description |
|---|---|---|---|
| order_id | Integer | FK(order.id), PK | |
| product_id | Integer | FK(product.id), PK | |
| quantity | Integer | Not Null, Default: 1 | |
| price | Float | Not Null | **Price snapshot at order time** |
| extended_warranty | Boolean | Default: False | |

#### PCBuild

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| user_id | Integer | FK(user.id), Not Null | Build creator |
| name | String(128) | Not Null | Configuration name |
| description | Text | Nullable | |
| is_public | Boolean | Default: False | Community visibility |
| created_at | DateTime | Default: utcnow | |
| updated_at | DateTime | Default: utcnow, onupdate: utcnow | |

#### build_components (Junction Table)

| Column | Type | Constraints | Description |
|---|---|---|---|
| build_id | Integer | FK(pc_build.id), PK | |
| product_id | Integer | FK(product.id), PK | |
| quantity | Integer | Not Null, Default: 1 | |

#### Review

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| rating | Integer | Not Null | 1-5 star rating |
| text | Text | Nullable | Review body |
| user_id | Integer | FK(user.id), Not Null | Reviewer |
| product_id | Integer | FK(product.id), Not Null | Reviewed product |
| order_id | Integer | FK(order.id), Nullable | Proof of purchase link |
| created_at | DateTime | Indexed, Default: utcnow | |

#### Message

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| sender_id | Integer | FK(user.id), Nullable | |
| recipient_id | Integer | FK(user.id), Nullable | |
| content | Text | Not Null | Message body (max 1000 chars) |
| timestamp | DateTime | Indexed, Default: utcnow | |
| is_read | Boolean | Default: False | |

#### Post (Blog)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| title | String(200) | Not Null | Article title |
| slug | String(200) | Unique, Not Null | URL path |
| content | Text | Not Null | Rich HTML content (sanitized) |
| author_id | Integer | FK(user.id), Not Null | |
| featured_image | String(256) | Nullable | Header image path |
| is_published | Boolean | Default: False | Draft/published toggle |
| created_at | DateTime | Default: utcnow | |
| updated_at | DateTime | Default: utcnow, onupdate: utcnow | |

#### Subscription (Newsletter)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| email | String(120) | Unique, Not Null | Subscriber email |
| created_at | DateTime | Default: utcnow | |

#### LagerProduct (Warehouse)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| name | String(128) | Not Null | |
| stock | Integer | Default: 0 | |
| purchase_price | Float | Nullable | Cost price |
| reservation_note | String(255) | Nullable | |
| internal_note | Text | Nullable | |
| for_company | Boolean | Default: False | |
| category_id | Integer | FK(lager_category.id), Not Null | |
| created_at | DateTime | Default: utcnow | |
| updated_at | DateTime | Default: utcnow, onupdate: utcnow | |

#### LagerCategory (Warehouse Categories)

| Column | Type | Constraints | Description |
|---|---|---|---|
| id | Integer | PK | |
| name | String(64) | Not Null | |
| slug | String(64) | Unique, Not Null | |
| parent_id | Integer | FK(lager_category.id), Nullable | Hierarchical |
| sort_order | Integer | Not Null, Default: 0 | |

---

## 6. Authentication & Authorization

### 6.1 Authentication Flow

```
Registration:
  User submits form (username, email, password, confirm_password)
    -> Server validates (unique username/email, password strength)
    -> Password hashed via Werkzeug generate_password_hash
    -> User record created with role='musterija'
    -> Auto-login via Flask-Login login_user()
    -> Redirect to homepage

Login:
  User submits email + password
    -> Rate limit check (5/min, 20/hour)
    -> Lookup user by email
    -> Check is_banned flag (reject if True)
    -> Verify password via check_password_hash
    -> Establish session via login_user()
    -> Redirect to 'next' URL or homepage

Logout:
  -> Flask-Login logout_user()
  -> Redirect to homepage
```

### 6.2 Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- Hashed using Werkzeug's PBKDF2-SHA256

### 6.3 Session Configuration

| Setting | Value | Purpose |
|---|---|---|
| SESSION_COOKIE_HTTPONLY | True | Prevents JavaScript access to session cookie |
| SESSION_COOKIE_SAMESITE | Lax | CSRF protection for cross-origin requests |
| SESSION_COOKIE_SECURE | True (production) | HTTPS-only cookie transmission |
| SESSION_COOKIE_NAME | sajborg_session | Custom cookie name |
| PERMANENT_SESSION_LIFETIME | 7 days (app.py) / 1 hour (middleware) | Session duration |
| SESSION_REFRESH_EACH_REQUEST | True | Prevents session fixation |

### 6.4 Role-Based Access Control

| Role | Serbian Name | Permissions |
|---|---|---|
| `musterija` | Customer | Browse, cart, checkout, orders, reviews, chat, PC builder |
| `distributer` | Distributor | Customer permissions + warehouse view (in-stock only) |
| `dobavljac` | Supplier | Customer permissions + full warehouse access |
| `admin` | Administrator | All permissions + admin panel |

### 6.5 Access Control Implementation

- **`@login_required`** - Flask-Login decorator, redirects unauthenticated users to login
- **`@admin_required`** - Custom decorator in `routes/admin/__init__.py`, checks `current_user.role == 'admin'`, returns 403 if not
- **Warehouse access** - Checked in route handler: role must be `distributer`, `dobavljac`, or `admin`
- **Self-protection** - Admins cannot change their own role or ban themselves

---

## 7. Routes & Endpoints

### 7.1 Public Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/` | `main.index` | Homepage with featured products & categories |
| GET | `/o-nama` | `main.about` | About page |
| GET | `/politika-privatnosti` | `main.privacy` | Privacy policy |
| GET | `/uslovi-koriscenja` | `main.terms` | Terms of service |
| GET | `/sitemap.xml` | `seo.sitemap` | XML sitemap (products, categories, posts) |
| GET | `/robots.txt` | `seo.robots` | Robots exclusion file |

### 7.2 Authentication Routes

| Method | Path | Handler | Rate Limit | Description |
|---|---|---|---|---|
| GET/POST | `/login` | `auth.login` | 5/min, 20/hour | User login |
| GET/POST | `/register` | `auth.register` | 3/hour, 10/day | User registration |
| GET | `/logout` | `auth.logout` | - | Session termination |
| GET/POST | `/profile` | `auth.profile` | - | Profile & address management |

### 7.3 Product Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/proizvodi` | `product.products` | Product listing with search, filters, sorting, pagination |
| GET | `/proizvodi/<category_slug>` | `product.products` | Category-filtered products |
| GET | `/product/<slug>` | `product.product_detail` | Product detail with images, specs, reviews |
| POST | `/product/<product_id>/add_review` | `product.add_review` | Submit product review (login required, delivered order required) |

### 7.4 Cart & Checkout Routes

| Method | Path | Handler | Rate Limit | Description |
|---|---|---|---|---|
| GET | `/cart` | `cart.view_cart` | - | Cart page with items, totals |
| POST | `/cart/update` | `cart.update_cart` | 30/min | Update quantity/warranty (AJAX) |
| POST | `/cart/remove/<item_id>` | `cart.remove_from_cart` | - | Remove item from cart |
| GET/POST | `/checkout` | `cart.checkout` | 10/hour | Shipping form & order placement |
| GET | `/checkout/success` | `cart.checkout_success` | - | Order confirmation |
| GET | `/checkout/cancel` | `cart.checkout_cancel` | - | Order cancellation page |

### 7.5 PC Builder Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/pc-builder/` | `builder.builder` | Builder interface |
| GET | `/pc-builder/components/<type>` | `builder.get_components` | Components by type (AJAX JSON) |
| POST | `/pc-builder/save` | `builder.save_build` | Save configuration (AJAX) |
| GET | `/pc-builder/load/<build_id>` | `builder.load_build` | Load saved build (AJAX JSON) |
| GET | `/pc-builder/build/<build_id>` | `builder.view_build` | View public build page |
| POST | `/pc-builder/build/<build_id>/delete` | `builder.delete_build` | Delete saved build |
| POST | `/pc-builder/build/<build_id>/add-to-cart` | `builder.add_build_to_cart` | Add all components to cart |
| POST | `/pc-builder/check-compatibility` | `builder.check_compatibility` | Compatibility check (AJAX JSON) |

### 7.6 Interaction Routes (AJAX)

| Method | Path | Handler | Rate Limit | Description |
|---|---|---|---|---|
| POST | `/interaction/subscribe` | `interaction.subscribe` | - | Newsletter subscription |
| POST | `/interaction/add-to-cart` | `interaction.add_to_cart` | 30/min | Add product to cart |
| GET | `/interaction/search-suggestions` | `interaction.search_suggestions` | - | Search autocomplete (JSON) |

### 7.7 Chat Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/chat/widget_data` | `chat.widget_data` | Chat initialization data |
| GET | `/chat/history/<user_id>` | `chat.get_history` | Message history |
| POST | `/chat/send` | `chat.send_message` | Send a message |
| GET | `/chat/unread_check` | `chat.unread_check` | Poll for new messages |
| POST | `/chat/delete/<user_id>` | `chat.delete_conversation` | Delete conversation (admin only) |

### 7.8 Blog Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/tech-magazin/` | `blog.blog_list` | All published posts |
| GET | `/tech-magazin/<slug>` | `blog.blog_post` | Single post detail |

### 7.9 Warehouse Routes

| Method | Path | Handler | Description |
|---|---|---|---|
| GET | `/lager/` | `lager.warehouse` | Inventory view (role-gated) |

### 7.10 Admin Routes

All admin routes are protected by `@admin_required` and prefixed with `/admin`.

**Dashboard:**
| Method | Path | Description |
|---|---|---|
| GET | `/admin/dashboard` | Stats overview (product count, order count, user count, recent orders) |

**Products:**
| Method | Path | Description |
|---|---|---|
| GET | `/admin/products` | Product list (search, filter, paginate) |
| GET/POST | `/admin/products/add` | Create product |
| GET/POST | `/admin/products/edit/<id>` | Edit product |
| POST | `/admin/products/delete/<id>` | Delete product |

**Categories:**
| Method | Path | Description |
|---|---|---|
| GET | `/admin/categories` | Category list |
| GET/POST | `/admin/categories/add` | Create category |
| GET/POST | `/admin/categories/edit/<id>` | Edit category (includes attribute schema management) |
| POST | `/admin/categories/delete/<id>` | Delete category (cascades to products) |

**Orders:**
| Method | Path | Description |
|---|---|---|
| GET | `/admin/orders` | Order list (search, filter by status, sort) |
| GET | `/admin/orders/<order_id>` | Order detail with items, prices, shipping |
| POST | `/admin/orders/update-status/<order_id>` | Change order status |

**Users:**
| Method | Path | Description |
|---|---|---|
| GET | `/admin/users` | User list (search, paginate) |
| POST | `/admin/users/update_role/<user_id>` | Change user role |
| POST | `/admin/users/delete/<user_id>` | Delete user |
| POST | `/admin/users/user/<user_id>/ban` | Ban user (blocks login) |
| POST | `/admin/users/user/<user_id>/unban` | Unban user |

**Blog:**
| Method | Path | Description |
|---|---|---|
| GET | `/admin/posts` | Post list |
| GET/POST | `/admin/posts/add` | Create post (Summernote editor) |
| GET/POST | `/admin/posts/edit/<id>` | Edit post |
| POST | `/admin/posts/delete/<id>` | Delete post |

**Product Images:**
| Method | Path | Description |
|---|---|---|
| Various | `/admin/product-images/*` | Upload, set primary, reorder, delete images |

**Bulk Import:**
| Method | Path | Description |
|---|---|---|
| GET/POST | `/admin/products/import` | Upload CSV/Excel for bulk product creation |

---

## 8. Business Logic & Flows

### 8.1 Currency Conversion & Pricing

```
Input: EUR price (from supplier)
Step 1: EUR -> BAM conversion:  bam = eur * 1.95583  (fixed rate)
Step 2: Apply markup:           final = bam * 1.15    (15% markup)
Step 3: Round to 2 decimals

Constants (config.py):
  EUR_TO_BAM_RATE = 1.95583
  MARKUP_PERCENTAGE = 15
  SHIPPING_COST = 10.0  (flat rate in KM)
```

### 8.2 Extended Warranty

- Available only for products with `condition == 'Novo'` (new items)
- Adds **10% markup** to the item price
- Tracked per `CartItem.extended_warranty` and persisted in `order_items.extended_warranty`
- Warranty toggle available in cart view

### 8.3 Shopping Cart Flow

```
1. ADD TO CART
   User clicks "Add to Cart" on product page or listing
   -> POST /interaction/add-to-cart (AJAX) or form submit
   -> If user not logged in: redirect to login
   -> Check product stock > 0
   -> If CartItem exists for this user+product: increment quantity
   -> Else: create new CartItem(user_id, product_id, quantity=1)
   -> Return success response

2. VIEW CART
   GET /cart
   -> Load user's CartItem records with product data
   -> Calculate per-item subtotal (price * quantity, +10% if warranty)
   -> Calculate cart total
   -> Add flat shipping cost (10 KM)
   -> Display cart page

3. UPDATE CART
   POST /cart/update (AJAX)
   -> Update quantity for specified item
   -> Toggle extended_warranty flag
   -> Recalculate totals
   -> Return updated data

4. REMOVE FROM CART
   POST /cart/remove/<item_id>
   -> Delete CartItem record
   -> Redirect back to cart

5. CHECKOUT
   GET /checkout
   -> Pre-fill form with user's saved address data
   -> Display order summary

   POST /checkout
   -> Validate shipping form
   -> Create Order record with:
     - Shipping address snapshot
     - Total amount (items + shipping)
     - Status: 'pending'
     - Payment method: 'cash_on_delivery'
   -> For each CartItem:
     - Create order_items entry with price snapshot
     - Decrement product stock
   -> Clear user's cart (delete all CartItems)
   -> Redirect to /checkout/success

6. ORDER CONFIRMATION
   GET /checkout/success
   -> Display order confirmation with order details
```

### 8.4 Order Lifecycle

```
pending -> preparing -> shipped -> delivered
  |          |           |          |
  +----------+-----------+----------+-> cancelled (from any state)

Status Transitions (admin only):
  pending     -> preparing, cancelled
  preparing   -> shipped, cancelled
  shipped     -> delivered, cancelled
  delivered   -> (terminal state)
  cancelled   -> (terminal state)

Side Effects:
  Status = 'delivered' -> Enables product reviews for this order's items
```

### 8.5 PC Builder Compatibility Engine

The compatibility checker (`utils.py:check_pc_build_compatibility`) reads product attributes from the dynamic attribute system to verify hardware compatibility:

```
1. CPU + MOTHERBOARD SOCKET CHECK
   - Read 'socket' attribute from CPU (e.g., "LGA1700")
   - Read 'socket' attribute from Motherboard (e.g., "LGA1700")
   - Compare case-insensitively
   - FAIL if mismatch

2. RAM + MOTHERBOARD TYPE CHECK
   - Read 'ram' attribute from RAM module (e.g., "DDR5")
   - Read 'ram' attribute from Motherboard (e.g., "DDR5")
   - Check if RAM type string is contained in motherboard's supported types
   - FAIL if incompatible

3. PSU WATTAGE CHECK
   - Sum 'tdp (w)' or 'tdp' attributes across all non-PSU components
   - Read 'wattage' attribute from PSU
   - FAIL if PSU wattage < total TDP * 1.20 (20% headroom requirement)

4. COMPLETENESS CHECK
   - Essential components: CPU, Motherboard, RAM, Storage, Power Supply, Case
   - WARN about any missing essential components
   - Report list of missing items

Result: (is_compatible: bool, messages: list[str])
```

### 8.6 Product Filtering & Search

```
Filters applied (all optional, composable):
  1. Category filter     -> Product.category_id == selected
                         -> Includes subcategory products
  2. Search query        -> Product.name ILIKE '%query%'
  3. Dynamic attributes  -> JOIN ProductAttributeValue, filter by attribute_id + value
  4. Price range         -> Product.price BETWEEN min AND max
  5. Stock filter        -> Product.stock > 0
  6. Visibility          -> Product.is_publicly_visible == True (always)

Sort Options:
  - Name ascending (name_asc)
  - Name descending (name_desc)
  - Price ascending (price_asc)
  - Price descending (price_desc)

Pagination: Server-side with configurable items per page
```

### 8.7 Review System

```
Eligibility:
  - User must be authenticated
  - User must have at least one Order with status='delivered' containing the product
  - One review per product per order

Submission:
  POST /product/<product_id>/add_review
  -> Validate rating (1-5) and optional text
  -> Verify delivered order exists for user+product
  -> Create Review(rating, text, user_id, product_id, order_id)

Display:
  - Product detail page shows all reviews
  - Product.average_rating computed property aggregates ratings
```

### 8.8 Chat System

```
Customer Flow:
  - Chat widget visible in bottom-right corner
  - Messages sent to admin user(s)
  - Polling for new messages via GET /chat/unread_check

Admin Flow:
  - Chat management in admin panel
  - View all active conversations
  - Reply to specific users
  - Delete conversations
  - Max message length: 1000 characters
```

### 8.9 Bulk Product Import

```
Supported Formats: CSV, Excel (.xls, .xlsx)

Required Columns: name, description, price, stock
Category Column: Either 'category_id' (numeric) or 'category_name' (text)
Optional Columns: image_url, specs, component_type

Validation:
  - All required columns present
  - Price is numeric and > 0
  - Stock is numeric and >= 0
  - Every row has a name and description
  - Category reference is valid

Process:
  1. Upload file via admin form
  2. Parse with pandas (CSV or Excel)
  3. Validate all rows
  4. If validation passes: create Product records
  5. If validation fails: return error with row number and message
```

### 8.10 SEO

```
Sitemap Generation (GET /sitemap.xml):
  - All publicly visible products with slugs
  - All public categories with slugs
  - All published blog posts with slugs
  - Static pages (homepage, about, privacy, terms)
  - XML format with lastmod, changefreq, priority

Robots.txt (GET /robots.txt):
  - Allow all crawlers
  - Reference sitemap URL

URL Strategy:
  - Products: /product/<slug>
  - Categories: /proizvodi/<category_slug>
  - Blog posts: /tech-magazin/<slug>
  - All slugs auto-generated from titles via python-slugify
```

---

## 9. Frontend Architecture

### 9.1 Template Hierarchy

```
base.html (Master Layout)
|-- Navbar (with category dropdown from global context, cart count, user menu)
|-- Flash messages display
|-- {% block content %} (page-specific content)
|-- Footer (newsletter signup, links, copyright)
|-- Global JS includes
|
|-- auth/login.html
|-- auth/register.html
|-- auth/profile.html
|
|-- shop/products.html         (product grid with sidebar filters)
|-- shop/product_detail.html   (image gallery, specs, reviews, add-to-cart)
|-- shop/cart.html             (cart table with quantity controls, warranty toggles)
|-- shop/checkout.html         (shipping form, order summary)
|
|-- pc_builder/builder.html    (interactive component selector)
|-- pc_builder/build_detail.html
|
|-- blog/blog_list.html        (post grid with featured images)
|-- blog/blog_post.html        (full article with sanitized HTML)
|
|-- admin/dashboard.html       (stats cards, recent orders table)
|-- admin/products/*.html      (CRUD forms, list views)
|-- admin/categories/*.html
|-- admin/orders/*.html
|-- admin/users/*.html
|-- admin/posts/*.html
|
|-- errors/403.html, 404.html, 500.html
```

### 9.2 Template Filters

| Filter | Usage | Description |
|---|---|---|
| `json_loads` | `{{ specs\|json_loads }}` | Parse JSON string to dict |
| `nl2br` | `{{ text\|nl2br }}` | Convert newlines to `<br>` tags |
| `bool_to_da_ne` | `{{ flag\|bool_to_da_ne }}` | Boolean -> "Da"/"Ne" |
| `sanitize_html` | `{{ content\|sanitize_html }}` | Bleach HTML sanitization |

### 9.3 Context Processor (Global Variables)

Available in all templates:

| Variable | Description |
|---|---|
| `all_categories` | Top-level public categories for navbar dropdown |
| `timedelta` | Python timedelta for template date math |
| `cache_buster` | Unix timestamp appended to asset URLs |

### 9.4 JavaScript Modules

| File | Responsibility |
|---|---|
| `main.js` | Global search bar autocomplete, utility functions |
| `cart.js` | AJAX cart operations: quantity +/-, warranty toggle, remove item, live total recalculation |
| `pc_builder.js` | Component type selection, AJAX component loading, compatibility check triggers, save/load builds |
| `product_detail.js` | Image gallery/lightbox, review form validation, add-to-cart handler |
| `admin.js` | Admin form validation, confirmation dialogs, bulk action handlers |
| `chat.js` | Chat widget toggle, message sending, polling for new messages, scroll-to-bottom |
| `modal_utils.js` | Reusable modal creation and management |

---

## 10. Admin Panel

### 10.1 Dashboard

- **Product count** (publicly visible only)
- **Order count** (total)
- **User count** (total)
- **Recent 5 orders** table with status badges

### 10.2 Product Management

- Searchable, paginated product list with category filter
- Create/edit form with:
  - Basic info (name, description, price, stock)
  - Category selection (determines available dynamic attributes)
  - Condition (Novo/Polovno) and availability status
  - Component type (for PC builder mapping)
  - Visibility toggle (public storefront vs hidden)
  - Featured product flag
  - Internal fields (purchase price, reservation notes, internal notes, for_company)
  - Dynamic attribute values (rendered based on category's attribute schema)
- Multi-image upload with primary selection and sort ordering
- Bulk import via CSV/Excel

### 10.3 Category Management

- Full CRUD with hierarchical parent-child support
- Category attribute schema builder:
  - Define attributes per category (name, type, sort order)
  - Types: string, int, float, bool, select
  - For `select` type: manage predefined options
- Featured flag for homepage display
- Component type assignment for PC builder integration
- Public/private visibility control

### 10.4 Order Management

- Searchable, filterable (by status), sortable order list
- Order detail view:
  - Customer info and shipping address
  - Line items with quantities, unit prices, warranty flags
  - Order total
- Status transition buttons (pending -> preparing -> shipped -> delivered / cancelled)

### 10.5 User Management

- Searchable, paginated user list
- Role assignment dropdown (musterija, distributer, dobavljac, admin)
- Ban/unban toggle (prevents user login when banned)
- Delete user
- Self-protection: admin cannot modify own role or ban themselves

### 10.6 Blog Management

- Post list with publish status
- Rich text editor (Summernote) for content
- Featured image upload
- Auto-generated slug from title
- Publish/unpublish toggle

---

## 11. Security

### 11.1 HTTP Security Headers

Applied to every response via `@app.after_request`:

| Header | Value | Purpose |
|---|---|---|
| X-Content-Type-Options | nosniff | Prevents MIME type sniffing |
| X-Frame-Options | SAMEORIGIN | Prevents clickjacking |
| X-XSS-Protection | 1; mode=block | Browser XSS filter |
| Strict-Transport-Security | max-age=31536000; includeSubDomains | Forces HTTPS (production only) |
| Content-Security-Policy | (see below) | Resource loading restrictions |
| Referrer-Policy | strict-origin-when-cross-origin | Controls referrer information |
| Permissions-Policy | Disables: geolocation, microphone, camera, USB, sensors | Browser feature restrictions |

### 11.2 Content Security Policy

```
default-src 'self';
script-src  'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://cdn.jsdelivr.net https://code.jquery.com;
style-src   'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com;
font-src    'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net;
img-src     'self' data: https: blob:;
connect-src 'self' https://api.stripe.com;
frame-src   'self' https://js.stripe.com;
object-src  'none';
base-uri    'self';
form-action 'self';
upgrade-insecure-requests;
```

### 11.3 CSRF Protection

- Flask-WTF CSRFProtect enabled globally
- Tokens required on all POST, PUT, PATCH, DELETE requests
- Token injected into all forms via `{{ form.hidden_tag() }}`
- AJAX requests include CSRF token in headers
- No time limit on tokens (`WTF_CSRF_TIME_LIMIT = None`)
- Specific endpoints exempted where necessary (e.g., PC builder compatibility check)

### 11.4 Rate Limiting

| Endpoint | Limit | Purpose |
|---|---|---|
| Global default | 200/day, 50/hour | General abuse prevention |
| Login | 5/min, 20/hour | Brute force protection |
| Registration | 3/hour, 10/day | Spam account prevention |
| Add to cart | 30/min | Bot prevention |
| Cart update | 30/min | Bot prevention |
| Checkout | 10/hour | Order abuse prevention |

Storage: In-memory (fixed-window strategy). Disabled in test config.

### 11.5 Input Validation

- **WTForms** validators on all form fields (length, required, email format, etc.)
- **Bleach** HTML sanitization for blog content (whitelist of safe tags and attributes)
- **SQLAlchemy** ORM parameterized queries (no raw SQL injection risk)
- **Werkzeug** secure filename generation for uploads
- **Custom** `secure_filename_custom()` in utils.py with additional path traversal prevention

### 11.6 File Upload Security

| Check | Image | Document |
|---|---|---|
| Allowed extensions | png, jpg, jpeg, gif, webp | pdf, doc, docx, txt |
| Max size | 5 MB | 10 MB |
| Empty file check | Yes | Yes |
| Filename sanitization | Yes (random token + ext) | Yes |
| Path traversal prevention | Yes (strip separators, dots) | Yes |

Global max content length: 16 MB (`MAX_CONTENT_LENGTH`).

### 11.7 Additional Protections

- **Open redirect prevention** - `is_safe_url()` validates redirect targets against host
- **Password hashing** - PBKDF2-SHA256 via Werkzeug
- **Account banning** - `is_banned` flag checked at login time
- **Auto-escaping** - Jinja2 auto-escapes all template output by default
- **ProxyFix** - Correctly handles X-Forwarded-For, X-Forwarded-Proto behind Nginx

---

## 12. Configuration & Environment

### 12.1 Configuration Classes

| Class | `DEBUG` | `TESTING` | Database | CSRF | Rate Limits |
|---|---|---|---|---|---|
| DevelopmentConfig | True | False | SQLite (instance/pcshop.db) | Enabled | Enabled |
| TestingConfig | False | True | SQLite (test.db) | **Disabled** | **Disabled** |
| ProductionConfig | False | False | From `DATABASE_URL` env var | Enabled | Enabled |

### 12.2 Environment Variables

**Required (Production):**

| Variable | Description |
|---|---|
| `SESSION_SECRET` | Flask secret key (min 16 chars, must not be default) |
| `STRIPE_SECRET_KEY` | Stripe API secret (must start with `sk_live_` in production) |
| `DATABASE_URL` | Database connection string (postgresql:// or mysql://) |

**Required (Development):**

| Variable | Description |
|---|---|
| `SESSION_SECRET` | Flask secret key (defaults to `dev-secret-key` if unset) |

**Optional / Recommended:**

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | development | Environment selector |
| `DEBUG` | false | Flask debug mode |
| `STRIPE_PUBLISHABLE_KEY` | - | Stripe frontend key |
| `MAIL_SERVER` | smtp.example.com | SMTP server |
| `MAIL_PORT` | 587 | SMTP port |
| `MAIL_USE_TLS` | true | TLS for email |
| `MAIL_USERNAME` | - | SMTP username |
| `MAIL_PASSWORD` | - | SMTP password |
| `MAIL_DEFAULT_SENDER` | no-reply@sajborg.com | From address |
| `SESSION_COOKIE_SECURE` | true | HTTPS-only cookies |
| `MAX_UPLOAD_SIZE` | 5242880 (5MB) | Upload size limit |
| `RATELIMIT_ENABLED` | true | Toggle rate limiting |
| `SENTRY_DSN` | - | Error tracking |

### 12.3 Environment Validation

The `env_validator.py` module runs at app startup:

1. Checks required variables per environment
2. Warns about recommended but missing variables
3. Validates variable formats:
   - SESSION_SECRET length >= 16
   - SESSION_SECRET not default in production
   - STRIPE_SECRET_KEY prefix matches environment (sk_test_ vs sk_live_)
   - DATABASE_URL starts with valid scheme (sqlite:///, postgresql://, mysql://)
4. **Exits with code 1** in production if required variables are missing
5. Prints warnings in development and continues

### 12.4 Business Constants

Defined in `config.py`:

```python
EUR_TO_BAM_RATE = 1.95583      # Fixed EUR to BAM exchange rate
MARKUP_PERCENTAGE = 15          # 15% markup on converted prices
SHIPPING_COST = 10.0            # Flat shipping cost in KM

COMPONENT_TYPES = [
    'CPU', 'Motherboard', 'RAM', 'GPU', 'Storage', 'Power Supply',
    'CPU Cooler', 'Case', 'Case Fans', 'Monitor', 'Keyboard', 'Mouse'
]

PRODUCT_CATEGORIES = [
    'CPUs', 'Motherboards', 'Memory', 'Graphics Cards', 'Storage',
    'Power Supplies', 'Cases', 'Cooling', 'Peripherals', 'Monitors',
    'Networking', 'Software'
]
```

---

## 13. Deployment

### 13.1 Production Architecture

```
Internet
  |
  v
Nginx (port 80/443)
  |-- Static files served directly (/static, /uploads)
  |-- SSL termination (Let's Encrypt)
  |-- Proxy headers (X-Real-IP, X-Forwarded-For, X-Forwarded-Proto)
  |
  v (Unix socket: /var/www/Sajborg/sajborg.sock)
Gunicorn (4 workers, 120s timeout)
  |
  v
Flask Application (wsgi.py -> create_app('production'))
  |
  v
PostgreSQL / SQLite
```

### 13.2 File Layout on Server

```
/var/www/Sajborg/              # Application root
  |-- venv/                    # Python virtual environment
  |-- instance/                # SQLite database (if used)
  |-- uploads/                 # User-uploaded files
  |-- static/                  # Static assets
  |-- .env                     # Environment variables (from .env.example)
  |-- sajborg.sock             # Gunicorn Unix socket

/etc/systemd/system/sajborg.service   # Systemd unit
/etc/nginx/sites-available/sajborg    # Nginx config
/etc/nginx/sites-enabled/sajborg      # Symlink to above
/var/log/gunicorn/                    # Application logs
/var/log/nginx/                       # Web server logs
```

### 13.3 Automated Deployment (deploy.sh)

The deployment script performs a 12-step automated setup on Ubuntu:

1. Update system packages
2. Install system dependencies (python3, pip, venv, nginx, certbot)
3. Create Python virtual environment
4. Install Python dependencies + Gunicorn
5. Create `.env` from template with generated secret key
6. Create instance/uploads directories
7. Initialize database (Flask-Migrate init, migrate, upgrade)
8. Set file permissions (www-data ownership)
9. Install and start systemd service
10. Configure Nginx (copy config, create symlink, test, restart)
11. Optional SSL setup via Certbot
12. Final health checks (Gunicorn running, Nginx running)

### 13.4 Nginx Configuration

- Listens on port 80 (with HTTPS redirect ready to uncomment)
- Serves `/static` and `/uploads` directly with 30-day cache headers
- Proxies all other requests to Gunicorn via Unix socket
- Security headers at the Nginx level (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- Client body size limit: 10 MB
- Proxy timeouts: 120 seconds (connect, send, read)

### 13.5 Gunicorn Configuration (sajborg.service)

```ini
Workers: 4
Bind: unix:/var/www/Sajborg/sajborg.sock
Timeout: 120 seconds
User/Group: www-data
Access log: /var/log/gunicorn/sajborg_access.log
Error log: /var/log/gunicorn/sajborg_error.log
Environment: FLASK_ENV=production (+ .env file)
```

### 13.6 Useful Management Commands

```bash
# Service management
sudo systemctl restart sajborg.service
sudo systemctl status sajborg.service
sudo journalctl -u sajborg.service -f

# Nginx
sudo systemctl restart nginx
sudo nginx -t
sudo tail -f /var/log/nginx/sajborg_error.log

# Database migrations
cd /var/www/Sajborg && source venv/bin/activate
flask db migrate -m "Description"
flask db upgrade
```

---

## 14. Testing

### 14.1 Test Suite Overview

- **Framework**: Pytest
- **Test count**: 126 tests
- **Coverage**: HTML report via `htmlcov/`

### 14.2 Test Categories (Markers)

| Marker | Description |
|---|---|
| `@pytest.mark.unit` | Isolated unit tests |
| `@pytest.mark.integration` | Integration tests with database |
| `@pytest.mark.auth` | Authentication & authorization tests |
| `@pytest.mark.cart` | Shopping cart functionality |
| `@pytest.mark.admin` | Admin panel operations |
| `@pytest.mark.security` | Security-specific tests |

### 14.3 Test Configuration

Uses `TestingConfig`:
- SQLite test database (`test.db`)
- CSRF disabled (`WTF_CSRF_ENABLED = False`)
- Rate limiting disabled (`RATELIMIT_ENABLED = False`)
- `TESTING = True`

### 14.4 Running Tests

```bash
# All tests
pytest

# Specific marker
pytest -m auth
pytest -m security

# With coverage
pytest --cov=. --cov-report=html
```

---

## 15. Third-Party Integrations

### 15.1 Stripe (Payment Processing)

- **Status**: SDK installed and configured, CSP allows Stripe JS/API
- **Current state**: Cash on delivery only; Stripe integration prepared but not active
- **Configuration**: `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` env vars
- **CSP allowances**: `js.stripe.com` (scripts, frames), `api.stripe.com` (connect)

### 15.2 Email (SMTP)

- **Status**: Configuration ready, not yet implemented
- **Settings**: MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD
- **Default sender**: no-reply@sajborg.com
- **Planned uses**: Order confirmations, password reset, newsletter

### 15.3 CDN Resources

- **Bootstrap CSS/JS**: cdn.jsdelivr.net
- **jQuery**: code.jquery.com
- **Google Fonts**: fonts.googleapis.com / fonts.gstatic.com
- **FontAwesome**: Vendored locally in static/vendor/

### 15.4 Sentry (Error Tracking)

- **Status**: Placeholder configuration (`SENTRY_DSN` in recommended env vars)
- **Not yet integrated** into the application code

---

*Generated from source code analysis of the Sajborg.com repository.*
