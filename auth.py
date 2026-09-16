from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()

        if len(phone) < 10 or not password:
            flash("شماره تلفن یا رمز عبور نامعتبر است.", "danger")
            return redirect(url_for('auth.register'))

        p_hash = generate_password_hash(password)
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (phone, password_hash, full_name) VALUES (?, ?, ?)",
                    (phone, p_hash, full_name)
                )
                conn.commit()
            flash("ثبت‌نام با موفقیت انجام شد. اکنون وارد شوید.", "success")
            return redirect(url_for('auth.login'))
        except Exception:
            flash("این شماره قبلاً در سیستم ثبت شده است.", "danger")

    return render_template('login.html', is_register=True)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_phone'] = user['phone']
            session['user_name'] = user['full_name']
            flash("خوش آمدید!", "success")
            return redirect(url_for('auth.profile'))
        
        flash("شماره موبایل یا رمز عبور اشتباه است.", "danger")

    return render_template('login.html', is_register=False)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        orders = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT 10", (session['user_id'],)).fetchall()
        txs = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (session['user_id'],)).fetchall()

    return render_template('profile.html', user=user, orders=orders, txs=txs)

