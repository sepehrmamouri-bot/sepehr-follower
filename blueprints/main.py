from flask import Blueprint, render_template, request, flash
from database import get_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    conn = get_db()
    services = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    return render_template('index.html', services=services)

@main_bp.route('/track', methods=['GET', 'POST'])
def track_order():
    order = None
    tracking_code = request.args.get('code', '')
    
    if request.method == 'POST':
        tracking_code = request.form.get('tracking_code', '').strip()

    if tracking_code:
        conn = get_db()
        order = conn.execute('SELECT * FROM orders WHERE tracking_code = ?', (tracking_code,)).fetchone()
        conn.close()
        if not order and request.method == 'POST':
            flash('سفارشی با این کد رهگیری پیدا نشد.', 'danger')

    return render_template('track.html', order=order, code=tracking_code)

