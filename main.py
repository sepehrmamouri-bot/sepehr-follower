from flask import Blueprint, render_template, request, jsonify
from database import get_connection

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services")
    all_services = cursor.fetchall()
    conn.close()

    services_by_cat = {
        'instagram': [],
        'telegram': [],
        'youtube': []
    }

    for s in all_services:
        cat = s['category'] if s['category'] in services_by_cat else 'instagram'
        services_by_cat[cat].append(dict(s))

    return render_template('index.html', services=services_by_cat)

@main_bp.route('/api/check-coupon', methods=['POST'])
def check_coupon():
    data = request.get_json() or {}
    code = data.get('code', '').strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT percent FROM coupons WHERE code = ? AND active = 1", (code,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({'valid': True, 'percent': row['percent']})
    return jsonify({'valid': False, 'message': 'کد تخفیف یافت نشد یا منقضی شده است.'})

