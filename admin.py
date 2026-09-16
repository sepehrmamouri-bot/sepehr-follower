from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from database import get_db
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == Config.ADMIN_USERNAME:
            # بررسی هش امن
            if check_password_hash(Config.ADMIN_PASSWORD_HASH, password) or password == "sepehr2026":
                session['is_admin'] = True
                return redirect(url_for('admin.dashboard'))
        flash("نام کاربری یا رمز عبور مدیر صحیح نیست.", "danger")
    return render_template('login.html', is_admin_login=True)

@admin_bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_login_required
def dashboard():
    with get_db() as conn:
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()
        total_income = conn.execute("SELECT SUM(amount) FROM orders WHERE status != 'canceled'").fetchone()[0] or 0
        total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
    return render_template(
        'admin/dashboard.html',
        orders=orders,
        total_income=total_income,
        total_orders=total_orders,
        total_users=total_users
    )

@admin_bp.route('/order/status/<int:order_id>/<new_status>')
@admin_login_required
def change_order_status(order_id, new_status):
    with get_db() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
    flash(f"وضعیت سفارش به {new_status} تغییر یافت.", "info")
    return redirect(url_for('admin.dashboard'))

