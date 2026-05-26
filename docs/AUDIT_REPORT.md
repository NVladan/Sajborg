# Sajborg.com - Full Project Audit Report

> Multi-agent audit performed by: Forge (Backend), Pixel (Frontend/UX), Vault (Database), Shield (Security), Deploy (Infrastructure)

---

## Table of Contents

1. [Database & Inventory Snapshot](#1-database--inventory-snapshot)
2. [Critical Issues](#2-critical-issues)
3. [Backend Findings (Forge)](#3-backend-findings-forge)
4. [UI/UX Findings (Pixel)](#4-uiux-findings-pixel)
5. [Database Findings (Vault)](#5-database-findings-vault)
6. [Security Findings (Shield)](#6-security-findings-shield)
7. [Infrastructure Findings (Deploy)](#7-infrastructure-findings-deploy)
8. [Prioritized Action Plan](#8-prioritized-action-plan)

---

## 1. Database & Inventory Snapshot

### Current Store Contents

| Category | Products | Price Range (KM) | In Stock | Component Type |
|---|---|---|---|---|
| Procesori (CPUs) | 16 | 95 - 515 | 9 | CPU |
| Maticne ploce (Motherboards) | 16 | 104 - 288 | 7 | Motherboard |
| Diskovi (Storage) | 15 | 43 - 507 | 8 | Storage |
| RAM memorija | 14 | 41 - 1,225 | 10 | RAM |
| Graficke kartice (GPUs) | 12 | 356 - 1,688 | 6 | GPU |
| CPU Kuleri (Coolers) | 11 | 27 - 97 | 9 | CPU Cooler |
| Napojne jedinice (PSUs) | 8 | 30 - 294 | 11 | Power Supply |
| Kucista (Cases) | 4 | 87 - 162 | 1 | Case |
| **TOTAL** | **96** | **27 - 1,688** | **61 total units** | |

### Key Stats

- **96 products** total, **42 publicly visible**, **42 in stock**, **27 featured**
- **95 New**, **1 Used** (Polovno)
- **8 categories**, all top-level (no subcategories used)
- **Brands**: AMD, Intel, ASUS, Gigabyte, MSI, ASRock, G.SKILL, Kingston, Corsair, DeepCool, Thermalright, etc.
- **13 users**, **3 orders**, **0 reviews**, **1 blog post**, **181 warehouse items**, **4 newsletter subscribers**

### Inventory Gaps

- **Cases**: Only 4 products, only 1 in stock - very limited selection
- **Monitors**: Category exists in config but **0 products** in database
- **Peripherals** (Keyboard, Mouse): Component types defined but **no category or products**
- **Networking, Software**: Listed in `PRODUCT_CATEGORIES` config but no products
- **No subcategories** used at all despite the schema supporting them
- **54 products hidden** (is_publicly_visible=False) - over half the catalog is invisible

---

## 2. Critical Issues

These require immediate attention:

### CRITICAL-1: Race Condition on Stock Decrement
**File**: `routes/cart.py` (checkout handler)
**Issue**: Stock is decremented without database-level locking. Two concurrent checkouts can oversell the same product.
```python
# Current (unsafe):
product.stock -= item.quantity
db.session.commit()

# Should use: SELECT FOR UPDATE or optimistic locking
```
**Impact**: Overselling products, negative stock values
**Fix**: Wrap checkout in a database transaction with `db.session.begin_nested()` and use `with_for_update()` on product queries.

### CRITICAL-2: No Transaction Wrapping on Order Creation
**File**: `routes/cart.py`
**Issue**: Order creation, stock decrement, and cart clearing are not wrapped in a single atomic transaction. A failure midway leaves the database in an inconsistent state (e.g., order created but stock not decremented, or stock decremented but cart not cleared).
**Fix**: Use explicit `db.session.begin()` / `db.session.commit()` / `db.session.rollback()` wrapping the entire checkout operation.

### CRITICAL-3: IDOR on Chat Messages
**File**: `routes/chat.py`
**Issue**: The `get_history/<user_id>` endpoint may allow any logged-in user to read another user's chat history by changing the user_id parameter. Needs authorization check that `current_user.id == user_id` or `current_user.role == 'admin'`.
**Fix**: Add explicit ownership or admin check.

### CRITICAL-4: Default Secret Key in Development
**File**: `app.py:30`, `config.py:11`
**Issue**: `SECRET_KEY` defaults to `'dev-secret-key'` when `SESSION_SECRET` env var is not set. If deployed without setting this, all sessions can be forged.
**Fix**: The env_validator warns but doesn't block in development. Consider failing loudly.

---

## 3. Backend Findings (Forge)

### HIGH Severity

**H1: Missing `@login_required` on sensitive routes**
- `routes/cart.py` - Some cart operations may be accessible without login
- `routes/pc_builder.py` - Save/delete build operations should verify authentication
- **Fix**: Audit every POST endpoint and ensure `@login_required` is present

**H2: No pagination on admin order/user lists**
- `routes/admin/order_routes.py`, `routes/admin/user_routes.py`
- Large datasets will cause performance issues and timeouts
- **Fix**: Add `.paginate()` to all admin list queries

**H3: Cart quantity not validated against stock**
- `routes/cart.py` and `routes/interaction.py`
- Users can add more items than available stock
- **Fix**: Check `requested_quantity <= product.stock` before adding/updating cart

**H4: No order total recalculation server-side**
- `routes/cart.py` (checkout)
- Total should be recalculated from cart items at checkout time, not trusted from client
- **Fix**: Always recalculate `calculate_order_total()` at checkout submission

**H5: `process_import_file` error handling**
- `utils.py:46-105`
- Generic `except Exception` catches everything including `KeyboardInterrupt`
- Missing validation for negative prices, extremely large stock values
- **Fix**: Use specific exception types, add range validation

### MEDIUM Severity

**M1: Duplicate product slug generation not handled**
- `routes/admin/product_routes.py`
- If two products have the same name, slug collision will cause a database IntegrityError
- **Fix**: Add slug uniqueness check with suffix increment (e.g., `product-name-2`)

**M2: EUR-to-BAM conversion not used consistently**
- `utils.py:8-12` defines `eur_to_bam()` but prices in the database are stored directly in BAM
- Unclear whether prices are entered in EUR and converted, or entered directly in BAM
- **Fix**: Clarify pricing workflow and document it

**M3: `check_pc_build_compatibility` fragile attribute lookups**
- `utils.py:108-198`
- Depends on exact attribute names ("socket", "ram", "tdp (w)") - case-sensitive matching
- If an admin misspells an attribute name, compatibility checks silently fail
- **Fix**: Normalize attribute names or use attribute IDs

**M4: Missing error pages for rate limit errors**
- `extensions.py` - Rate limiter returns JSON 429 but no custom HTML page
- **Fix**: Add 429 error handler in `app.py`

**M5: Blog content not length-validated**
- `routes/admin/blog_routes.py`
- No maximum content length on blog posts - could store very large HTML blobs
- **Fix**: Add `Length(max=...)` validator on content field

**M6: Flash messages use hardcoded strings**
- Throughout all route files
- Mix of Bosnian and English in flash messages
- **Fix**: Use a constants file or i18n framework

### LOW Severity

**L1: `app.py:115` - `cache_buster=int(time.time())` regenerates on every request**
- This defeats browser caching entirely since every URL is unique
- **Fix**: Use file modification time or app version hash instead

**L2: Dead code in config.py**
- `PRODUCT_CATEGORIES` list at line 33 is defined but never referenced in any route
- **Fix**: Remove or use it for validation

**L3: Unused import `Flask-Admin`**
- `requirements.txt:6` - Flask-Admin is installed but never imported or used
- **Fix**: Remove from requirements if not planned

**L4: `seo_routes.py` sitemap may be slow**
- Queries all products and categories on every request
- **Fix**: Cache the sitemap XML with a TTL

---

## 4. UI/UX Findings (Pixel)

### Accessibility (A11Y)

**A1: Missing ARIA labels throughout** [HIGH]
- `templates/base.html` - Navbar toggle button missing `aria-label`
- `templates/shop/products.html` - Filter form inputs missing `aria-label` or associated `<label>`
- `templates/shop/cart.html` - Quantity +/- buttons have no accessible text
- All icon-only buttons (delete, edit) rely solely on visual icons
- **Fix**: Add `aria-label` to every interactive element without visible text

**A2: No skip navigation link** [MEDIUM]
- `templates/base.html` - No "Skip to main content" link for keyboard users
- **Fix**: Add hidden skip link as first focusable element

**A3: Missing alt text on product images** [HIGH]
- `templates/shop/product_detail.html`, `templates/shop/products.html`
- Images use empty or missing `alt` attributes
- **Fix**: Use product name as alt text: `alt="{{ product.name }}"`

**A4: Form error messages not linked to inputs** [MEDIUM]
- Error messages displayed separately from their form fields
- Screen readers can't associate errors with specific inputs
- **Fix**: Use `aria-describedby` linking errors to inputs

**A5: Color contrast issues** [MEDIUM]
- Light gray text on white backgrounds in several places
- Price text and availability badges may not meet WCAG AA contrast ratios
- **Fix**: Audit with contrast checker, ensure 4.5:1 ratio minimum

### Responsive Design & Mobile

**R1: Tables not responsive** [HIGH]
- `templates/shop/cart.html` - Cart table overflows on mobile
- `templates/admin/*.html` - All admin tables overflow on small screens
- **Fix**: Wrap tables in `.table-responsive` or use card layouts on mobile

**R2: Filter sidebar not collapsible on mobile** [HIGH]
- `templates/shop/products.html` - Category/attribute filters take up full screen width on mobile
- **Fix**: Make filters collapsible behind a "Filters" button on mobile

**R3: Chat widget may overlap content on mobile** [MEDIUM]
- `static/js/chat.js` - Fixed position chat widget can cover important content
- **Fix**: Make chat widget draggable or collapsible to a small icon on mobile

**R4: PC Builder not mobile-friendly** [MEDIUM]
- `templates/pc_builder/builder.html` - Multi-column component selector doesn't adapt
- **Fix**: Stack columns vertically on small screens

### UX Anti-Patterns

**U1: No loading indicators on AJAX operations** [HIGH]
- `static/js/cart.js` - No spinner when updating quantities
- `static/js/pc_builder.js` - No loading state when checking compatibility
- `static/js/main.js` - No loading state on search suggestions
- **Fix**: Add spinner/loading overlay during AJAX calls

**U2: No empty state handling** [HIGH]
- `templates/shop/cart.html` - Empty cart shows just an empty table
- `templates/shop/products.html` - No products found shows blank area
- Search results - No "no results" illustration or suggestion
- **Fix**: Add friendly empty states with illustrations and CTAs

**U3: No confirmation dialogs for destructive actions** [HIGH]
- Delete product, delete user, remove cart item - happen immediately on click
- **Fix**: Add confirmation modals: "Are you sure you want to delete X?"

**U4: Missing breadcrumbs** [MEDIUM]
- Product pages, category pages, admin pages - no breadcrumb navigation
- Users can't orient themselves in the hierarchy
- **Fix**: Add breadcrumb component: Home > Category > Product

**U5: No "Back to Top" button** [LOW]
- Long product listing pages require scrolling all the way up
- **Fix**: Add floating "back to top" button after scrolling past fold

**U6: No recently viewed products** [LOW]
- No tracking of user's browsing history
- **Fix**: Store in localStorage and show on product pages

**U7: Cart doesn't show product images** [MEDIUM]
- `templates/shop/cart.html` - Only shows product names, no thumbnails
- **Fix**: Add small product image in cart table

### Form UX

**F1: No inline validation** [MEDIUM]
- Registration, checkout, product forms - errors only shown after submission
- **Fix**: Add client-side validation with real-time feedback

**F2: Checkout form doesn't save progress** [MEDIUM]
- If submission fails, all data is lost
- **Fix**: Pre-fill from user profile (partially done) and persist form state

**F3: Search has no keyboard shortcut** [LOW]
- No Ctrl+K or `/` to focus search bar
- **Fix**: Add keyboard shortcut for power users

### SEO in Templates

**S1: Missing Open Graph meta tags** [MEDIUM]
- `templates/base.html` - No `og:title`, `og:description`, `og:image`
- Products shared on social media show no preview
- **Fix**: Add OG tags in `<head>` block, override per page

**S2: Missing structured data (JSON-LD)** [MEDIUM]
- Product pages have no Schema.org `Product` markup
- Google can't show rich product snippets in search
- **Fix**: Add JSON-LD `Product` schema with price, availability, reviews

**S3: Missing canonical URLs** [LOW]
- No `<link rel="canonical">` tags
- Potential duplicate content issues with filter/sort URL parameters
- **Fix**: Add canonical URL to every page

### Visual Consistency

**V1: Mixed button styles** [LOW]
- Some pages use `btn-primary`, others `btn-success`, `btn-info` for similar actions
- No consistent button hierarchy

**V2: Inconsistent spacing** [LOW]
- Margins/padding vary between similar page sections
- Admin panel and storefront use different spacing scales

**V3: No design system / component library** [LOW]
- Each template reinvents common patterns (cards, badges, tables)
- **Fix**: Create reusable Jinja2 macros for common components

---

## 5. Database Findings (Vault)

### HIGH Severity

**D1: No database-level constraints on critical fields**
- `models.py:100` - `Product.price` is `Float` with no CHECK constraint for `price > 0`
- `models.py:101` - `Product.stock` has no CHECK constraint for `stock >= 0`
- `models.py:310` - `Review.rating` has no CHECK constraint for `1 <= rating <= 5`
- **Fix**: Add `CheckConstraint` to model definitions

**D2: Float used for monetary values**
- `Product.price`, `Product.purchase_price`, `Order.total_amount`, `order_items.price`
- Float arithmetic causes precision errors (e.g., 0.1 + 0.2 != 0.3)
- **Fix**: Use `Numeric(10, 2)` (Decimal) for all monetary columns

**D3: N+1 query on product listing**
- `routes/product.py` - Loading products with their categories, images, and attribute values
- Each product triggers separate queries for related objects
- **Fix**: Use `joinedload()` or `subqueryload()` for eager loading:
  ```python
  Product.query.options(
      joinedload(Product.category),
      joinedload(Product.images),
      subqueryload(Product.attribute_values)
  )
  ```

**D4: N+1 query on admin order list**
- `routes/admin/order_routes.py` - Loading orders with user details
- **Fix**: Eager load user relationship

**D5: Missing index on Product.slug**
- `models.py:113` - `slug` is `unique=True` which creates an index in most databases, but worth verifying
- Also missing index on `Product.name` for search queries (ILIKE)
- **Fix**: Add `db.Index('idx_product_name', 'name')` for search performance

### MEDIUM Severity

**D6: `order_items` junction table missing own primary key**
- Using composite PK of `(order_id, product_id)` means a user can't order the same product twice in one order at different prices (e.g., one with warranty, one without)
- **Fix**: Add auto-increment `id` column as PK

**D7: `PCBuild.components` lacks quantity tracking per component**
- `build_components` has `quantity` but the relationship doesn't easily expose it
- **Fix**: Use an Association Object pattern instead of secondary table

**D8: No soft delete on any model**
- Deleting products that have been ordered creates orphan records in `order_items`
- **Fix**: Add `is_deleted` flag to Product, or use `ON DELETE SET NULL` with nullable FK

**D9: `LagerProduct` and `Product` are completely separate**
- Warehouse inventory and store inventory are disconnected
- No way to sync stock between warehouse and storefront
- **Fix**: Either merge models or add a foreign key linking them

**D10: Missing `updated_at` on several models**
- `CartItem`, `Review`, `Message`, `Subscription` lack update timestamps
- **Fix**: Add `updated_at` column for audit trail

### LOW Severity

**D11: `Product.specs` (Text) appears unused**
- Legacy JSON field that's been replaced by the dynamic attribute system
- **Fix**: Remove after confirming no code references it

**D12: No database-level unique constraint on `(user_id, product_id, order_id)` for Review**
- Application code may check, but the database doesn't enforce one-review-per-product-per-order
- **Fix**: Add `UniqueConstraint('user_id', 'product_id', 'order_id')`

---

## 6. Security Findings (Shield)

### CRITICAL

**SEC-1: Default secret key in source code**
- `app.py:30` and `config.py:11`: `SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key')`
- If deployed without setting `SESSION_SECRET`, sessions can be forged
- **Remediation**: Remove default value, fail on startup if not set in production

**SEC-2: Stock race condition (see CRITICAL-1 above)**
- Can lead to financial loss from overselling

**SEC-3: IDOR vulnerabilities in chat and orders**
- `routes/chat.py` - Chat history accessible by manipulating user_id
- `routes/cart.py` - Verify cart item belongs to current_user before allowing removal
- **Remediation**: Always verify `object.user_id == current_user.id`

### HIGH

**SEC-4: Duplicate CSP headers**
- Both `security.py` and `security_middleware.py` set CSP headers in `@after_request`
- The second one overwrites the first, potentially leaving gaps
- CSP in `security_middleware.py:42-49` is LESS restrictive than `security.py:50-62` (missing Stripe, missing `object-src 'none'`, missing `form-action`, missing `upgrade-insecure-requests`)
- **Remediation**: Remove one of the duplicate security header modules

**SEC-5: `'unsafe-inline'` and `'unsafe-eval'` in CSP script-src**
- Allows inline scripts and eval(), undermining XSS protection
- **Remediation**: Move all inline JS to external files, use nonces for necessary inline scripts, remove `'unsafe-eval'`

**SEC-6: No CSRF token on AJAX requests verification**
- `static/js/cart.js`, `static/js/pc_builder.js` - AJAX POST requests may not consistently include CSRF tokens
- Some endpoints exempted from CSRF (`/pc-builder/check-compatibility`)
- **Remediation**: Ensure all AJAX calls include `X-CSRFToken` header

**SEC-7: File upload - no content-type validation**
- `utils.py:223-256` - Only checks file extension, not actual file content (MIME type)
- An attacker could upload a PHP/Python script with a `.jpg` extension
- **Remediation**: Add magic byte / MIME type validation using `python-magic` or Pillow's `Image.verify()`

**SEC-8: Missing rate limits on sensitive admin endpoints**
- Admin product/user/order operations have no rate limits
- A compromised admin session could rapidly exfiltrate or modify data
- **Remediation**: Add rate limits to admin blueprint

### MEDIUM

**SEC-9: Password reset not implemented**
- No forgot-password flow exists
- Users locked out of accounts have no self-service recovery
- **Remediation**: Implement token-based password reset via email

**SEC-10: No account lockout after failed logins**
- Rate limiting (5/min) slows brute force but doesn't lock the account
- **Remediation**: Lock account after N failed attempts, require admin unlock or timed cooldown

**SEC-11: User enumeration via registration**
- Registration form reveals whether an email/username already exists
- **Remediation**: Use generic "If this email exists, we sent a verification" message

**SEC-12: No Content-Disposition header on uploaded files**
- Uploaded images served without `Content-Disposition: inline` or `attachment`
- Could allow stored XSS via SVG uploads (if allowed)
- **Remediation**: Set `Content-Disposition` header and consider disallowing SVG

**SEC-13: Session lifetime inconsistency**
- `app.py:35` sets `PERMANENT_SESSION_LIFETIME = 7 days`
- `security_middleware.py:86` overrides to `3600` (1 hour)
- **Remediation**: Pick one value and set it in one place

### LOW

**SEC-14: No security.txt**
- Missing `/.well-known/security.txt` for responsible disclosure
- **Remediation**: Add security contact information

**SEC-15: No Subresource Integrity (SRI) on CDN scripts**
- External JS/CSS loaded from CDN without `integrity` attribute
- **Remediation**: Add SRI hashes to all `<script src="cdn...">` tags

**SEC-16: `DEBUG=True` in development runs with production database risk**
- No guard against accidentally running debug mode with production DB
- **Remediation**: Check `DATABASE_URL` prefix when `DEBUG=True`

---

## 7. Infrastructure Findings (Deploy)

### HIGH

**I1: No health check endpoint**
- No `/health` or `/status` route for monitoring tools
- Load balancers, uptime monitors can't verify app is working
- **Fix**: Add a simple health check route that verifies DB connectivity

**I2: No database backup strategy**
- No backup script, no cron job, no point-in-time recovery
- **Fix**: Add automated daily backup script (pg_dump for PostgreSQL, sqlite3 .backup for SQLite)

**I3: No log rotation**
- Gunicorn logs at `/var/log/gunicorn/` will grow unbounded
- **Fix**: Add logrotate configuration

**I4: Nginx missing gzip compression**
- `nginx_sajborg.conf` doesn't enable gzip
- All HTML, CSS, JS sent uncompressed
- **Fix**: Add `gzip on; gzip_types text/html text/css application/javascript application/json;`

**I5: No CI/CD pipeline**
- No GitHub Actions, no automated testing on push, no automated deployment
- **Fix**: Add `.github/workflows/ci.yml` with test + lint + deploy stages

### MEDIUM

**I6: Gunicorn worker type is sync (default)**
- `sajborg.service` uses default sync workers
- Can't handle slow clients efficiently
- **Fix**: Consider `--worker-class=gthread` or `gevent` for better concurrency

**I7: No connection pooling configuration**
- SQLAlchemy defaults may not be optimal for production
- **Fix**: Configure `SQLALCHEMY_ENGINE_OPTIONS` with `pool_size`, `pool_recycle`, `pool_pre_ping`

**I8: Static files served by Gunicorn in development**
- No WhiteNoise or similar for development static file serving
- **Fix**: Add WhiteNoise middleware or use Flask's built-in static serving only in dev

**I9: No `.env` validation for Stripe keys format**
- `env_validator.py` checks prefix but not key length
- **Fix**: Add length validation for API keys

**I10: `deploy.sh` not idempotent**
- Running twice may cause issues (re-creating symlinks, re-running migrations)
- Parts use `|| true` to suppress errors which hides real problems
- **Fix**: Add idempotency checks (if exists, skip)

### LOW

**I11: Missing `--preload` flag for Gunicorn**
- Workers don't share loaded application code
- **Fix**: Add `--preload` to reduce memory usage

**I12: No monitoring/alerting setup**
- No Prometheus metrics, no error alerting, no uptime monitoring
- **Fix**: Add `/metrics` endpoint and integrate with monitoring stack

**I13: Requirements not using hash pinning**
- `requirements.txt` has versions but no hash verification
- **Fix**: Use `pip-compile` with `--generate-hashes` for supply chain security

**I14: Missing `robots.txt` for staging/preview environments**
- Only one robots.txt that allows all crawlers
- **Fix**: Disallow all crawlers on non-production environments

---

## 8. Prioritized Action Plan

### Phase 1: Critical Fixes (Do Now)

| # | Issue | Effort | Impact |
|---|---|---|---|
| 1 | Fix stock race condition with DB locking | Medium | Prevents overselling |
| 2 | Wrap checkout in atomic transaction | Medium | Prevents data corruption |
| 3 | Fix IDOR in chat and cart routes | Low | Prevents data leaks |
| 4 | Remove duplicate security header module | Low | Fixes CSP inconsistency |
| 5 | Remove default secret key fallback | Low | Prevents session forgery |
| 6 | Use Decimal instead of Float for money | Medium | Prevents pricing errors |

### Phase 2: High Priority (This Sprint)

| # | Issue | Effort | Impact |
|---|---|---|---|
| 7 | Add eager loading to fix N+1 queries | Medium | Major performance gain |
| 8 | Add CHECK constraints to DB | Low | Data integrity |
| 9 | Validate cart quantity against stock | Low | Prevents overselling |
| 10 | Add loading spinners to AJAX operations | Low | UX improvement |
| 11 | Add responsive table wrappers | Low | Mobile usability |
| 12 | Add empty state handling | Medium | UX improvement |
| 13 | Add confirmation dialogs for deletes | Low | Prevents accidents |
| 14 | Add ARIA labels to interactive elements | Medium | Accessibility |
| 15 | Add file content-type validation | Low | Security hardening |
| 16 | Add health check endpoint | Low | Monitoring readiness |

### Phase 3: Medium Priority (Next Sprint)

| # | Issue | Effort | Impact |
|---|---|---|---|
| 17 | Add Open Graph meta tags | Low | Social sharing |
| 18 | Add JSON-LD structured data | Medium | SEO / rich snippets |
| 19 | Add breadcrumb navigation | Medium | UX / SEO |
| 20 | Implement password reset flow | High | User self-service |
| 21 | Add inline form validation | Medium | UX improvement |
| 22 | Make filters collapsible on mobile | Medium | Mobile UX |
| 23 | Add cart product thumbnails | Low | Visual UX |
| 24 | Add Nginx gzip compression | Low | Performance |
| 25 | Add database backup script | Medium | Data safety |
| 26 | Add log rotation | Low | Operations |
| 27 | Add rate limits to admin routes | Low | Security |
| 28 | Add database connection pooling | Low | Performance |

### Phase 4: Improvements (Backlog)

| # | Issue | Effort | Impact |
|---|---|---|---|
| 29 | Add CI/CD pipeline | High | Dev workflow |
| 30 | Remove `'unsafe-inline'` from CSP | High | Security hardening |
| 31 | Add SRI hashes to CDN resources | Low | Supply chain security |
| 32 | Add product comparison feature | High | User feature |
| 33 | Add recently viewed products | Medium | User feature |
| 34 | Link Lager (warehouse) to Product model | High | Inventory sync |
| 35 | Add monitors/peripherals categories | Low | Catalog expansion |
| 36 | Set up error tracking (Sentry) | Medium | Observability |
| 37 | Add `security.txt` | Low | Responsible disclosure |
| 38 | Create reusable Jinja2 component macros | Medium | Code quality |
| 39 | Fix cache_buster to use file hash | Low | Caching efficiency |
| 40 | Clean up unused deps (Flask-Admin) | Low | Maintenance |

---

*Report generated by multi-agent audit team. All findings based on static code analysis.*
