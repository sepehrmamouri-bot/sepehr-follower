# -*- coding: utf-8 -*-
"""
پروژه جامع سپهر فالوور (Sepehr Follower Pro)
طراحی دیجی‌کالا + منطق فروش ایران فالوور
"""
import os
import sqlite3
import random
import string
import datetime
from functools import wraps
from flask import (
    Flask, request, session, redirect, url_for,
    render_template_string, Response, jsonify, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sepehr_follower_super_secret_key_2026")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sepehr_follower.db")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123456")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            old_price INTEGER,
            features TEXT,
            badge TEXT,
            is_special INTEGER DEFAULT 0
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE NOT NULL,
            package_id INTEGER,
            package_title TEXT,
            category TEXT,
            target_input TEXT NOT NULL,
            phone TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            ref_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            excerpt TEXT,
            content TEXT,
            author TEXT DEFAULT 'سپهر فالوور',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute("SELECT COUNT(*) FROM packages")
        if cursor.fetchone()[0] == 0:
            initial_packages = [
                ('follower_ir', '۱,۰۰۰ فالوور ایرانی واقعی', 1000, 189000, 260000, 'پروفایل کامل ایرانی | سرعت ارسال طبیعی | ضمانت جبران ریزش ۳۰ روزه | بدون نیاز به پسورد', 'شگفت‌انگیز', 1),
                ('follower_ir', '۲,۵۰۰ فالوور ایرانی باکیفیت', 2500, 445000, 590000, 'کاربران فعال اینستاگرام | ورود به اکسپلور | پشتیبانی اختصاصی | بدون پسورد', 'پرفروش', 0),
                ('follower_ir', '۵,۰۰۰ فالوور ایرانی طلایی', 5000, 850000, 1150000, 'کیفیت تضمینی VIP | مناسب پیج‌های تجاری | بونوس هدیه لایک | پشتیبانی ۲۴ ساعته', 'پیشنهاد ویژه', 1),
                ('follower_cheap', '۱,۰۰۰ فالوور اقتصادی', 1000, 68000, 95000, 'استارت فوری و سریع | ارزان‌ترین نرخ بازار | مناسب بالا بردن اعتبار پیج', 'ارزان', 0),
                ('follower_cheap', '۵,۰۰۰ فالوور میکس اقتصادی', 5000, 310000, 430000, 'تحویل سریع اتوماتیک | بدون نیاز به پسورد | کیفیت استاندارد', 'اقتصادی', 0),
                ('like', '۱,۰۰۰ لایک ایرانی واقعی', 1000, 49000, 75000, 'پروفایل‌های ایرانی | افزایش ایمپرشن و ریچ | شروع کمتر از ۵ دقیقه', 'محبوب', 1),
                ('like', '۵,۰۰۰ لایک ارگانیک', 5000, 215000, 290000, 'پخش تدریجی و طبیعی | کمک به رفتن به اکسپلور | پشتیبانی سریع', 'ویژه اکسپلور', 0),
                ('view', '۵,۰۰۰ بازدید ویدیو / ریلز', 5000, 24000, 39000, 'افزایش بازدید ویدیو و Reels | استارت آنی زیر ۲ دقیقه | بسیار ارزان', 'فوری', 0),
                ('view', '۲۰,۰۰۰ ویو میلیونی ریلز', 20000, 89000, 140000, 'پوشش الگوریتم ریلز اینستاگرام | تحویل آنی خودکار | تضمین کیفیت', 'شگفت‌انگیز', 1),
                ('comment', '۱۰۰ کامنت مرتبط فارسی', 100, 79000, 110000, 'متن‌های مثبت و دلخواه | پروفایل‌های معتبر فارسی | افزایش چشمگیر تعامل', 'تخصصی', 0)
            ]
            for p in initial_packages:
                cursor.execute(
                    "INSERT INTO packages (category, title, quantity, price, old_price, features, badge, is_special) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    p
                )
        conn.commit()

init_db()

def generate_tracking_code():
    chars = string.ascii_uppercase + string.digits
    return 'SPF-' + ''.join(random.choices(chars, k=8))

# قالب HTML ریسپانسیو با ظاهر دیجی‌کالا و ایران‌فالوور
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title or "سپهر فالوور | خرید فالوور، لایک و ویو ارزان و فوری اینستاگرام" }}</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #ef4056;
            --primary-dark: #cc253a;
            --secondary: #008eb2;
            --dark: #242529;
            --gray-bg: #f5f5f7;
            --border: #e0e0e2;
            --success: #00a049;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Vazirmatn', sans-serif; }
        body { background: var(--gray-bg); color: var(--dark); line-height: 1.6; padding-bottom: 70px; }
        header { background: #fff; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }
        .top-bar { background: var(--primary); color: #fff; text-align: center; font-size: 0.85rem; padding: 6px; }
        .nav-container { max-width: 1200px; margin: auto; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: 900; color: var(--primary); text-decoration: none; display: flex; align-items: center; gap: 8px; }
        .nav-links a { margin-right: 18px; text-decoration: none; color: #424750; font-weight: 500; font-size: 0.95rem; }
        .nav-links a:hover { color: var(--primary); }
        .hero { background: linear-gradient(135deg, #242529 0%, #17181c 100%); color: #fff; padding: 45px 20px; text-align: center; }
        .hero h1 { font-size: 2rem; margin-bottom: 12px; color: #fff; }
        .hero p { font-size: 1.05rem; color: #b5b8c2; max-width: 650px; margin: auto; }
        .container { max-width: 1200px; margin: 25px auto; padding: 0 15px; }
        .section-title { font-size: 1.4rem; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; }
        .card { background: #fff; border: 1px solid var(--border); border-radius: 12px; padding: 18px; position: relative; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.06); border-color: var(--primary); }
        .badge { position: absolute; top: 12px; left: 12px; background: #fef0f2; color: var(--primary); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; }
        .card-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; margin-top: 15px; }
        .features { list-style: none; font-size: 0.85rem; color: #62666d; margin-bottom: 20px; flex-grow: 1; }
        .features li { margin-bottom: 6px; display: flex; align-items: center; gap: 6px; }
        .features li i { color: var(--success); font-size: 0.8rem; }
        .price-box { margin-bottom: 14px; text-align: left; }
        .old-price { font-size: 0.85rem; color: #9e9e9e; text-decoration: line-through; }
        .price { font-size: 1.3rem; font-weight: 900; color: var(--dark); }
        .price span { font-size: 0.8rem; font-weight: 500; }
        .btn-buy { background: var(--primary); color: #fff; border: none; padding: 10px; border-radius: 8px; font-weight: 700; width: 100%; cursor: pointer; text-align: center; text-decoration: none; font-size: 0.95rem; transition: background 0.2s; }
        .btn-buy:hover { background: var(--primary-dark); }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 1000; align-items: center; justify-content: center; padding: 15px; }
        .modal-content { background: #fff; width: 100%; max-width: 440px; border-radius: 14px; padding: 22px; position: relative; }
        .close-modal { position: absolute; top: 12px; left: 15px; font-size: 1.3rem; cursor: pointer; color: #888; }
        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; font-size: 0.85rem; margin-bottom: 6px; font-weight: 600; }
        .form-group input { width: 100%; padding: 11px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; }
        .mobile-nav { display: none; position: fixed; bottom: 0; left: 0; right: 0; background: #fff; border-top: 1px solid var(--border); padding: 8px 0; justify-content: space-around; z-index: 99; }
        .mobile-nav a { color: #62666d; text-decoration: none; font-size: 0.75rem; text-align: center; display: flex; flex-direction: column; align-items: center; }
        .mobile-nav a i { font-size: 1.1rem; margin-bottom: 3px; }
        @media(max-width: 768px) {
            .nav-links { display: none; }
            .mobile-nav { display: flex; }
        }
    </style>
</head>
<body>
    <header>
        <div class="top-bar">🔥 ۴۰٪ تخفیف ویژه برای تمامی سفارش‌های اول با کد تخفیف ویژه!</div>
        <div class="nav-container">
            <a href="/" class="logo"><i class="fa-solid fa-rocket"></i> سپهر فالوور</a>
            <div class="nav-links">
                <a href="/"><i class="fa fa-home"></i> صفحه اصلی</a>
                <a href="/track"><i class="fa fa-search"></i> پیگیری سفارش</a>
                <a href="#services"><i class="fa fa-layer-group"></i> تعرفه‌ها</a>
            </div>
        </div>
    </header>

    <div class="hero">
        <h1>معتبرترین سامانه خرید فالوور و لایک واقعی اینستاگرام</h1>
        <p>تحویل کاملاً آنی، بدون نیاز به رمز عبور پیج و با ضمانت ۳۰ روزه بازگشت وجه</p>
    </div>

    <div class="container" id="services">
        <h2 class="section-title"><i class="fa-solid fa-fire" style="color: var(--primary);"></i> پرفروش‌ترین بسته‌های اینستاگرام</h2>
        <div class="grid">
            {% for pkg in packages %}
            <div class="card">
                {% if pkg.badge %}<span class="badge">{{ pkg.badge }}</span>{% endif %}
                <div class="card-title">{{ pkg.title }}</div>
                <ul class="features">
                    {% for feat in pkg.features.split('|') %}
                    <li><i class="fa fa-check-circle"></i> {{ feat.strip() }}</li>
                    {% endfor %}
                </ul>
                <div class="price-box">
                    {% if pkg.old_price %}
                    <div class="old-price">{{ "{:,}".format(pkg.old_price) }} تومان</div>
                    {% endif %}
                    <div class="price">{{ "{:,}".format(pkg.price) }} <span>تومان</span></div>
                </div>
                <button class="btn-buy" onclick="openOrderModal('{{ pkg.id }}', '{{ pkg.title }}', '{{ pkg.price }}')">
                    <i class="fa fa-shopping-cart"></i> سفارش آنی
                </button>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- مودال ثبت سفارش -->
    <div id="orderModal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeOrderModal()">&times;</span>
            <h3 id="modalPkgTitle" style="font-size: 1.1rem; margin-bottom: 12px;"></h3>
            <p id="modalPkgPrice" style="color: var(--primary); font-weight: 700; margin-bottom: 16px;"></p>
            <form action="/order" method="POST">
                <input type="hidden" name="package_id" id="modalPkgId">
                <div class="form-group">
                    <label>آیدی پیج یا لینک پست:</label>
                    <input type="text" name="target" placeholder="sepehr_follower@" required>
                </div>
                <div class="form-group">
                    <label>شماره تماس (جهت دریافت کد رهگیری):</label>
                    <input type="tel" name="phone" placeholder="0912..." required>
                </div>
                <button type="submit" class="btn-buy" style="margin-top: 10px;">ثبت و پرداخت نهایی</button>
            </form>
        </div>
    </div>

    <div class="mobile-nav">
        <a href="/"><i class="fa fa-home"></i>خانه</a>
        <a href="#services"><i class="fa fa-shopping-bag"></i>خدمات</a>
        <a href="/track"><i class="fa fa-search"></i>پیگیری</a>
    </div>

    <script>
        function openOrderModal(id, title, price) {
            document.getElementById('modalPkgId').value = id;
            document.getElementById('modalPkgTitle').innerText = title;
            document.getElementById('modalPkgPrice').innerText = Number(price).toLocaleString('fa-IR') + ' تومان';
            document.getElementById('orderModal').style.display = 'flex';
        }
        function closeOrderModal() {
            document.getElementById('orderModal').style.display = 'none';
        }
        window.onclick = function(e) {
            if(e.target == document.getElementById('orderModal')) closeOrderModal();
        }
    </script>
</body>
</html>
"""

# صفحه اصلی
@app.route('/')
def index():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages")
        packages = cursor.fetchall()
    return render_template_string(BASE_TEMPLATE, packages=packages)

# ثبت سفارش
@app.route('/order', methods=['POST'])
def create_order():
    package_id = request.form.get('package_id')
    target = request.form.get('target', '').strip()
    phone = request.form.get('phone', '').strip()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM packages WHERE id = ?", (package_id,))
        pkg = cursor.fetchone()
        if not pkg:
            return "پکیج یافت نشد", 404

        tracking = generate_tracking_code()
        cursor.execute('''
        INSERT INTO orders (tracking_code, package_id, package_title, category, target_input, phone, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
        ''', (tracking, pkg['id'], pkg['title'], pkg['category'], target, phone, pkg['price']))
        conn.commit()

    return f"""
    <div style="text-align: center; padding: 40px; font-family: sans-serif; direction: rtl;">
        <h2 style="color: #00a049;">سفارش شما با موفقیت ثبت شد!</h2>
        <p>کد پیگیری شما: <b>{tracking}</b></p>
        <p>پکیج: {pkg['title']}</p>
        <a href="/track" style="color: #ef4056; text-decoration: none; font-weight: bold;">مشاهده وضعیت سفارش</a>
    </div>
    """

# پیگیری سفارش
@app.route('/track', methods=['GET', 'POST'])
def track():
    order = None
    if request.method == 'POST':
        code = request.form.get('tracking_code', '').strip().upper()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE tracking_code = ?", (code,))
            order = cursor.fetchone()

    track_html = """
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>پیگیری سفارش | سپهر فالوور</title>
        <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
        <style>
            * { box-sizing: border-box; font-family: 'Vazirmatn', sans-serif; }
            body { background: #f5f5f7; padding: 30px 15px; }
            .box { max-width: 500px; margin: auto; background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
            input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; margin: 10px 0; }
            button { width: 100%; background: #ef4056; color: #fff; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
            .res { margin-top: 20px; background: #f8f9fa; padding: 15px; border-radius: 8px; border-right: 4px solid #00a049; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>پیگیری سفارش</h2>
            <form method="POST">
                <input type="text" name="tracking_code" placeholder="کد رهگیری مثلا SPF-XXXX" required>
                <button type="submit">استعلام وضعیت</button>
            </form>
            {% if order %}
            <div class="res">
                <p><b>کد پیگیری:</b> {{ order.tracking_code }}</p>
                <p><b>محصول:</b> {{ order.package_title }}</p>
                <p><b>هدف:</b> {{ order.target_input }}</p>
                <p><b>وضعیت:</b> {{ order.status }}</p>
            </div>
            {% endif %}
            <p style="margin-top: 15px; text-align: center;"><a href="/" style="color: #ef4056; text-decoration: none;">بازگشت به صفحه اصلی</a></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(track_html, order=order)

if __name__ == '__main__':
    app.run(debug=True)

