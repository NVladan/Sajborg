from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from extensions import db, limiter
from flask_wtf.csrf import generate_csrf
from flask import session
from models import User
from forms.auth_forms import LoginForm, RegistrationForm, ProfileForm

auth_bp = Blueprint('auth', __name__)


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
            if user is None or not user.check_password(form.password.data):
                flash('Nevažeći email ili lozinka', 'danger')
                return redirect(url_for('auth.login'))

            # --- POČETAK IZMENE ---
            # Provera da li je korisnik banovan
            if user.is_banned:
                flash('Vaš nalog je suspendovan. Molimo kontaktirajte administratora.', 'danger')
                return redirect(url_for('auth.login'))
            # --- KRAJ IZMENE ---

            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')

            return redirect(next_page)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'danger')

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

        flash('Vaš nalog je uspešno kreiran! Sada se možete prijaviti.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Registracija', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Uspešno ste se odjavili.', 'info')
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
        flash('Vaš profil je uspešno ažuriran!', 'success')
        return redirect(url_for('auth.profile'))

    # Get user orders
    orders = current_user.orders

    return render_template('auth/profile.html', title='Profil', form=form, orders=orders)