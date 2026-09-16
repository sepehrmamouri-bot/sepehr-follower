import string, random
from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from database import get_db
from payment import gateway
from smm_api import smm_client

order_bp = Blueprint('order', __name__, url_prefix='/order')

def make_tracking_code():
    chars = string.ascii_uppercase + string.digits
    return 'SPF-' + ''.join(random.choices(chars, k=8))

@order_bp.route('/create', methods=['POST'])
def create_order():
    pkg_id = request.form.get('package_id')
    service_id = request.form.get('service_id')
    target = request.form.get('target', '').strip()
    phone = request.form.get('phone', '').strip()
    quantity = int(request.form.get('quantity', 0) or 0)

    with get_db() as conn:
        if pkg_id:
            pkg = conn.execute("SELECT * FROM packages WHERE id = ?", (pkg_id,)).fetchone()
            if not pkg:
                flash("پکیج مورد نظر یافت نشد.", "danger")
                return redirect(url_for('main.index'))
            amount = pkg['price']
            quantity = pkg['quantity']
            title = pkg['title']
            category = pkg['category']
            smm_sid = None
        elif service_id:
            srv = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
            if not srv:
                flash("سرویس انتخابی نامعتبر است.", "danger")
                return redirect(url_for('main.services'))
            if quantity < srv['min_order'] or quantity > srv['max_order']:
                flash(f"تعداد سفارش باید بین {srv['min_order']} تا {srv['max_order']} باشد.", "danger")
                return redirect(url_for('main.services'))
            amount = int((srv['price_per_1000'] / 1000) * quantity)
            title = srv['name']
            category = srv['category']
            smm_sid = srv['smm_service_id']
        else:
            flash("خطای درخواست.", "danger")
            return redirect(url_for('main.index'))

        tracking = make_tracking_code()
        user_id = session.get('user_id')

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (
                tracking_code, user_id, service_id, package_id, package_title,
                category, target_input, quantity, amount, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (tracking, user_id, service_id, pkg_id, title, category, target, quantity, amount))
        order_id = cursor.lastrowid
        conn.commit()

    # ارسال به زرین‌پال
    res = gateway.request_payment(
        amount_toman=amount,
        description=f"سفارش {title} - {tracking}",
        phone=phone,
        callback_url=url_for('order.verify_payment', _external=True)
    )

    if res['success']:
        with get_db() as conn:
            conn.execute("UPDATE orders SET payment_authority = ? WHERE id = ?", (res['authority'], order_id))
            conn.commit()
        return redirect(res['url'])
    else:
        # در صورت نبود اینترنت در تست محلی، مستقیماً تایید فرضی صادر شود
        flash(f"کد پیگیری شما: {tracking} (در حالت تستی)", "info")
        return redirect(url_for('main.track_order', code=tracking))

@order_bp.route('/verify')
def verify_payment():
    authority = request.args.get('Authority')
    status = request.args.get('Status')

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE payment_authority = ?", (authority,)).fetchone()
        if not order:
            flash("سفارش یافت نشد.", "danger")
            return redirect(url_for('main.index'))

        if status == 'OK':
            ver = gateway.verify_payment(authority, order['amount'])
            if ver['success']:
                ref_id = str(ver.get('ref_id'))
                # ارسال سفارش به پنل مادر SMM
                smm_resp = smm_client.create_order(
                    service_id=order['service_id'] or 1,
                    link=order['target_input'],
                    quantity=order['quantity']
                )
                smm_order_id = str(smm_resp.get('order', ''))

                conn.execute('''
                    UPDATE orders 
                    SET status = 'processing', payment_ref_id = ?, smm_order_id = ?
                    WHERE id = ?
                ''', (ref_id, smm_order_id, order['id']))
                conn.commit()

                flash("پرداخت با موفقیت انجام و سفارش به سیستم ارسال شد!", "success")
                return redirect(url_for('main.track_order', code=order['tracking_code']))

        conn.execute("UPDATE orders SET status = 'canceled' WHERE id = ?", (order['id'],))
        conn.commit()
        flash("پرداخت ناموفق بود یا لغو گردید.", "danger")
        return redirect(url_for('main.index'))

