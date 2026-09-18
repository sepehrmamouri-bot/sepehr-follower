from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import database
import uuid
import datetime

app = Flask(__name__)
app.secret_key = "sepehr-follower-super-secret-ninja-key"

# اطمینان از مقداردهی اولیه دیتابیس
database.init_database()

# ----------------- مسیرهای اصلی سایت (بدون تغییر) -----------------

@app.route('/')
def index():
    conn = database.get_db()
    packages = conn.execute("SELECT * FROM packages WHERE is_active = 1").fetchall()
    # دریافت ۳ مقاله آخر برای نمایش احتمالی در فوتر یا سئو
    recent_articles = conn.execute("SELECT * FROM articles ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()
    return render_template('index.html', packages=packages, recent_articles=recent_articles)

@app.route('/order', methods=['POST'])
def create_order():
    service_id = request.form.get('service_id')
    target_link = request.form.get('target_link', '').strip()
    phone = request.form.get('phone', '').strip()
    coupon_code = request.form.get('coupon', '').strip()

    if not service_id or not target_link:
        flash("لطفاً اطلاعات سرویس و لینک را به درستی وارد کنید.", "danger")
        return redirect(url_for('index'))

    conn = database.get_db()
    package = conn.execute("SELECT * FROM packages WHERE id = ?", (service_id,)).fetchone()
    if not package:
        conn.close()
        flash("سرویس انتخاب شده معتبر نیست.", "danger")
        return redirect(url_for('index'))

    price = package['price']

    # بررسی کد تخفیف
    if coupon_code:
        coupon = conn.execute("SELECT * FROM coupons WHERE code = ? AND is_active = 1", (coupon_code,)).fetchone()
        if coupon:
            discount = int(price * (coupon['discount_percent'] / 100))
            price = max(0, price - discount)

    tracking_code = f"SPF-{uuid.uuid4().hex[:6].upper()}"

    conn.execute('''
        INSERT INTO orders (tracking_code, service_title, target_link, phone, amount, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (tracking_code, package['title'], target_link, phone, price, 'در انتظار پرداخت'))
    conn.commit()
    conn.close()

    return redirect(url_for('payment_gateway', tracking_code=tracking_code))

@app.route('/pay/<tracking_code>')
def payment_gateway(tracking_code):
    conn = database.get_db()
    order = conn.execute("SELECT * FROM orders WHERE tracking_code = ?", (tracking_code,)).fetchone()
    conn.close()
    if not order:
        return "سفارش یافت نشد", 404
    return render_template('payment_gateway.html', order=order)

@app.route('/pay/callback', methods=['POST'])
def payment_callback():
    tracking_code = request.form.get('tracking_code')
    status = request.form.get('status')
    payment_ref = f"SHP-{uuid.uuid4().hex[:8].upper()}"

    conn = database.get_db()
    if status == 'success':
        conn.execute('''
            UPDATE orders 
            SET status = 'در حال انجام (ارسال خودکار)', payment_ref = ? 
            WHERE tracking_code = ?
        ''', (payment_ref, tracking_code))
    else:
        conn.execute("UPDATE orders SET status = 'پرداخت ناموفق' WHERE tracking_code = ?", (tracking_code,))
    
    conn.commit()
    order = conn.execute("SELECT * FROM orders WHERE tracking_code = ?", (tracking_code,)).fetchone()
    conn.close()

    return render_template('receipt.html', order=order, success=(status == 'success'))

@app.route('/track', methods=['GET', 'POST'])
def track():
    order = None
    if request.method == 'POST':
        code = request.form.get('tracking_code', '').strip().upper()
        conn = database.get_db()
        order = conn.execute("SELECT * FROM orders WHERE tracking_code = ?", (code,)).fetchone()
        conn.close()
        if not order:
            flash("سفارشی با این کد پیگیری پیدا نشد.", "danger")
    return render_template('track.html', order=order)

@app.route('/admin')
def admin_panel():
    conn = database.get_db()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    total_sales = conn.execute("SELECT SUM(amount) FROM orders WHERE status != 'پرداخت ناموفق' AND status != 'در انتظار پرداخت'").fetchone()[0] or 0
    total_orders = len(orders)
    conn.close()
    return render_template('admin.html', orders=orders, total_sales=total_sales, total_orders=total_orders)


# ----------------- ماژول‌های سئو و وبلاگ (SEO & Blog Engine) -----------------

@app.route('/blog')
def blog_index():
    conn = database.get_db()
    articles = conn.execute("SELECT * FROM articles ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('blog.html', articles=articles)

@app.route('/blog/<slug>')
def article_detail(slug):
    conn = database.get_db()
    # افزایش بازدید
    conn.execute("UPDATE articles SET views = views + 1 WHERE slug = ?", (slug,))
    conn.commit()

    article = conn.execute("SELECT * FROM articles WHERE slug = ?", (slug,)).fetchone()
    if not article:
        conn.close()
        return "مقاله مورد نظر یافت نشد!", 404

    related_articles = conn.execute("SELECT * FROM articles WHERE id != ? ORDER BY id DESC LIMIT 3", (article['id'],)).fetchall()
    packages = conn.execute("SELECT * FROM packages WHERE is_active = 1 LIMIT 3").fetchall()
    conn.close()

    return render_template('article.html', article=article, related=related_articles, packages=packages)

# نقشه سایت برای گوگل سرچ کنسول (Google Search Console XML Sitemap)
@app.route('/sitemap.xml')
def sitemap():
    conn = database.get_db()
    articles = conn.execute("SELECT slug, created_at FROM articles").fetchall()
    conn.close()

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # صفحه اصلی
    xml.append('<url><loc>https://sepehrfollower.pythonanywhere.com/</loc><priority>1.0</priority><changefreq>daily</changefreq></url>')
    # صفحه پیگیری
    xml.append('<url><loc>https://sepehrfollower.pythonanywhere.com/track</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    # آرشیو مقالات
    xml.append('<url><loc>https://sepehrfollower.pythonanywhere.com/blog</loc><priority>0.9</priority><changefreq>daily</changefreq></url>')

    # صفحات تکی مقالات سئویی
    for art in articles:
        xml.append(f'''<url>
            <loc>https://sepehrfollower.pythonanywhere.com/blog/{art['slug']}</loc>
            <priority>0.85</priority>
            <changefreq>weekly</changefreq>
        </url>''')

    xml.append('</urlset>')
    return Response("\n".join(xml), mimetype='application/xml')

# فایل robots.txt جهت هدایت ربات‌های گوگل
@app.route('/robots.txt')
def robots():
    content = "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /pay/\n\nSitemap: https://sepehrfollower.pythonanywhere.com/sitemap.xml"
    return Response(content, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)

