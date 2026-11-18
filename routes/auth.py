from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from extensions import db, limiter
from flask_wtf.csrf import generate_csrf
from flask import session
from models import User, Order, Product, order_items
from forms.auth_forms import LoginForm, RegistrationForm, ProfileForm

MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

auth_bp = Blueprint('auth', __name__)


def safe_next(value):
    """Povratak samo na lokalnu putanju ('/proizvodi/…'); sve ostalo vodi na početnu."""
    if (value and value.startswith('/') and not value.startswith('//')
            and '\\' not in value and urlparse(value).netloc == ''):
        return value
    return url_for('main.index')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
@limiter.limit("20 per hour", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()

            # Check account lockout
            if user and user.locked_until and user.locked_until > datetime.utcnow():
                remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
                flash(f'Nalog je privremeno zaključan. Pokušajte ponovo za {remaining} minuta.', 'danger')
                return redirect(url_for('auth.login'))

            if user is None or not user.check_password(form.password.data):
                # Track failed login attempts
                if user:
                    user.failed_login_count = (user.failed_login_count or 0) + 1
                    if user.failed_login_count >= MAX_FAILED_LOGINS:
                        user.locked_until = datetime.utcnow() + LOCKOUT_DURATION
                        db.session.commit()
                        flash(f'Previše neuspješnih pokušaja. Nalog je zaključan na 15 minuta.', 'danger')
                        return redirect(url_for('auth.login'))
                    db.session.commit()
                flash('Email ili lozinka nisu tačni.', 'danger')
                return redirect(url_for('auth.login', next=request.args.get('next')))

            # Provera da li je korisnik banovan
            if user.is_banned:
                flash('Vaš nalog je suspendovan. Molimo kontaktirajte administratora.', 'danger')
                return redirect(url_for('auth.login'))

            # Reset failed login counter on successful login
            user.failed_login_count = 0
            user.locked_until = None
            db.session.commit()

            login_user(user, remember=form.remember.data)
            next_page = safe_next(request.args.get('next'))

            return redirect(next_page)

    return render_template('auth/login.html', title='Prijava', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour", methods=["POST"])
@limiter.limit("10 per day", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.is_subscribed = form.subscribe.data
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Nalog je napravljen i prijavljeni ste.', 'success')
        return redirect(safe_next(request.args.get('next')))

    return render_template('auth/register.html', title='Registracija', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Odjavljeni ste.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    if request.method == 'GET':
        # Pre-populate form with user data
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.address.data = current_user.address
        form.city.data = current_user.city
        form.postal_code.data = current_user.postal_code
        form.country.data = current_user.country
        form.phone_number.data = current_user.phone_number
        form.is_subscribed.data = current_user.is_subscribed

    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.address = form.address.data
        current_user.city = form.city.data
        current_user.postal_code = form.postal_code.data
        current_user.country = form.country.data
        current_user.phone_number = form.phone_number.data
        current_user.is_subscribed = form.is_subscribed.data

        db.session.commit()
        flash('Podaci su sačuvani.', 'success')
        return redirect(url_for('auth.profile'))

    # Narudžbe sa stvarnim stavkama (cijena i količina iz trenutka narudžbe), najnovije prvo
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    order_lines = {}
    if orders:
        rows = db.session.execute(
            db.select(order_items.c.order_id, order_items.c.quantity, order_items.c.price,
                      order_items.c.extended_warranty, Product)
            .join(Product, Product.id == order_items.c.product_id)
            .where(order_items.c.order_id.in_([o.id for o in orders]))
        ).all()
        for order_id, quantity, price, warranty, product in rows:
            order_lines.setdefault(order_id, []).append(
                {'product': product, 'quantity': quantity, 'price': price, 'warranty': warranty})

    return render_template('auth/profile.html', title='Profil', form=form, orders=orders,
                           order_lines=order_lines, builds=current_user.pc_builds)