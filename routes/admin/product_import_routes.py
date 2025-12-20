import pandas as pd
from flask import render_template, redirect, url_for, flash
from forms.product_forms import ImportForm
from . import admin_bp, admin_required


@admin_bp.route('/import', methods=['GET', 'POST'])
@admin_required
def import_products():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            flash('Fajl je otpremljen i proizvodi se uvoze u pozadini.', 'info')
            return redirect(url_for('admin.products'))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
            flash('Fajl je otpremljen i proizvodi se uvoze u pozadini.', 'info')
            return redirect(url_for('admin.products'))
        else:
            flash('Molimo Vas da otpremite važeći CSV ili Excel fajl.', 'warning')
    return render_template('admin/import.html',
                           title='Uvoz Proizvoda',
                           form=form)