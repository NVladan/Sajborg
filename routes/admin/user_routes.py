from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from extensions import db
from models import User
from . import admin_bp, admin_required


@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')

    query = User.query
    if search_query:
        query = query.filter(
            (User.username.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        )

    users_pagination = query.order_by(User.username.asc()).paginate(page=page, per_page=10, error_out=False)

    return render_template('admin/users.html',
                           title='Upravljanje Korisnicima',
                           users=users_pagination,
                           search_query=search_query)


@admin_bp.route('/users/update_role/<int:user_id>', methods=['POST'])
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    # Ne možete menjati ulogu sami sebi
    if user.id == current_user.id:
        flash('Ne možete menjati sopstvenu ulogu.', 'danger')
        return redirect(url_for('admin.users'))

    if new_role in ['musterija', 'distributer', 'dobavljac', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Uloga za korisnika {user.username} je uspešno ažurirana.', 'success')
    else:
        flash('Nevažeća uloga.', 'danger')

    return redirect(url_for('admin.users'))


@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Ne možete obrisati sopstveni administratorski nalog.', 'danger')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Korisnik je uspešno obrisan.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/<int:user_id>/ban', methods=['POST'])
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Ne možete banovati sami sebe.', 'danger')
        return redirect(url_for('admin.users'))

    if user.role == 'admin':
        flash('Ne možete banovati drugog administratora.', 'danger')
        return redirect(url_for('admin.users'))

    user.is_banned = True
    db.session.commit()
    flash(f'Korisnik {user.username} je uspešno banovan.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/user/<int:user_id>/unban', methods=['POST'])
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash(f'Korisnik {user.username} je uspešno odblokiran.', 'success')
    return redirect(url_for('admin.users'))