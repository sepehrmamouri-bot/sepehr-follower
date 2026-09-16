import random
import string
from flask import Blueprint, request, redirect, url_for, flash
from database import get_db

order_bp = Blueprint('order', __name__)

def generate_tracking_code():
    chars = string.ascii_uppercase + string.digits
    return 'SPF-' + ''.join(random.choices(chars, k=8))

@order_bp.route('/order', methods=['POST'])
def create_order():
    service_id = request.form.get('service_id')
    target_link = request.form.get('target_link', '').strip()
    phone = request.form.get('phone', '').strip()
    coupon_code = request.form.get('coupon_code', '').strip()

    if not service_id or not target_link or not phone:
        flash('لطفاً تمامی فیلدهای الزامی را پر کنید.', 'danger')
        return redirect(url_for('main.index'))

    conn = get_db()
    service = conn.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()

    if not service:
        conn.close()
        flash('سرویس انتخاب شده معتبر نمی‌باشد.', 'danger')
        return redirect(url_for('main.index'))

    final_price = service['price']

    # اعمال کوپن تخفیف
    if coupon_code:
        coupon = conn.execute('SELECT * FROM coupons WHERE code = ? AND is_active = 1', (coupon_code,)).fetchone()
        if coupon:
            discount = (final_price * coupon['discount_percent']) // 100
            final_price = max(0, final_price - discount)
            flash(f'کد تخفیف {coupon["discount_percent"]}٪ اعمال شد.', 'success')
        else:
            flash('کد تخفیف وارد شده نامعتبر است.', 'warning')

    tracking_code = generate_tracking_code()

    conn.execute('''
        INSERT INTO orders (tracking_code, service_name, target_link, phone, amount, status)
        VALUES (?, ?, ?, ?, ?, 'completed')
    ''', (tracking_code, service['title'], target_link, phone, final_price))
    conn.commit()
    conn.close()

    flash(f'سفارش شما با موفقیت ثبت شد! کد پیگیری: {tracking_code}', 'success')
    return redirect(url_for('main.track_order', code=tracking_code))

