
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config import Config
from database import get_db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('با موفقیت وارد شدید.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')

    return render_template('admin_login.html')

@admin_bp.route('/')
def dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin.login'))

    conn = get_db()
    orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    services = conn.execute('SELECT * FROM services').fetchall()
    total_sales = conn.execute('SELECT SUM(amount) FROM orders').fetchone()[0] or 0
    orders_count = len(orders)
    conn.close()

    return render_template('admin.html', orders=orders, services=services, total_sales=total_sales, orders_count=orders_count)

@admin_bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin.login'))

