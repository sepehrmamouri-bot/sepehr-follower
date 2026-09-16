# -*- coding: utf-8 -*-
"""
سپهر فالوور (Sepehr Follower) - نسخه کامل و دقیقا مشابه ایران‌فالوور
پشتیبانی از منوی کشویی سه خطی موبایل، تب‌بندی خدمات، پنل ادمین و بلاگ
"""
import os
import sqlite3
import random
import string
from functools import wraps
from flask import (
    Flask, request, session, redirect, url_for,
    render_template_string, jsonify, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sepehr_follower_iran_style_2026_key")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sepehr_follower.db")

ADMIN_USER = "admin"
ADMIN_PASS_HASH = generate_password_hash("sepehr2026")

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
            badge TEXT
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            excerpt TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # مقداردهی اولیه پکیج‌ها در صورت خالی بودن دیتابیس
        cursor.execute("SELECT COUNT(*) FROM packages")
        if cursor.fetchone()[0] == 0:
            pkgs = [
                ('follower_ir', '۱,۰۰۰ فالوور ایرانی واقعی', 1000, 189000, 260000, 'پروفایل ایرانی | سرعت ارگانیک | کیفیت VIP | بدون پسورد', 'پیشنهاد ویژه'),
                ('follower_ir', '۲,۵۰۰ فالوور ایرانی فعال', 2500, 445000, 590000, 'کاربران فعال | ضمانت ۳۰ روزه | افزایش ریچ پیج | تحویل سریع', 'پرفروش'),
                ('follower_ir', '۵,۰۰۰ فالوور ایرانی طلایی', 5000, 850000, 1150000, 'تضمین عدم ریزش | هدیه ۵۰۰ لایک | پشتیبانی اختصاصی', 'ویژه اکسپلور'),
                ('follower_cheap', '۱,۰۰۰ فالوور اقتصادی', 1000, 68000, 95000, 'استارت فوری | ارزان‌ترین نرخ | مناسب اعتبار اولیه', 'اقتصادی'),
                ('follower_cheap', '۵,۰۰۰ فالوور میکسی ارزان', 5000, 310000, 430000, 'سرعت ارسال بالا | بدون نیاز به رمز عبور', 'ارزان'),
                ('like', '۱,۰۰۰ لایک ایرانی واقعی', 1000, 49000, 75000, 'سرعت آنی | ورود به اکسپلور | کیفیت عالی', 'محبوب'),
                ('like', '۵,۰۰۰ لایک ایرانی و فعال', 5000, 215000, 290000, 'پخش طبیعی روی پست | افزایش ایمپرشن', 'پیشنهاد مدیر'),
                ('view', '۵,۰۰۰ ویو و بازدید ریلز', 5000, 24000, 39000, 'ارسال آنی کمتر از ۵ دقیقه | ارزان و باکیفیت', 'فوری'),
                ('view', '۲۰,۰۰۰ ویو میلیونی ریلز', 20000, 89000, 140000, 'بهترین کیفیت برای اکسپلور | تحویل اتوماتیک', 'شگفت‌انگیز'),
                ('comment', '۱۰۰ کامنت سفارشی فارسی', 100, 79000, 110000, 'متن‌های دلخواه فارسی | حساب‌های معتبر', 'تخصصی')
            ]
            for p in pkgs:
                cursor.execute("INSERT INTO packages (category, title, quantity, price, old_price, features, badge) VALUES (?, ?, ?, ?, ?, ?, ?)", p)
        
        cursor.execute("SELECT COUNT(*) FROM blog")
        if cursor.fetchone()[0] == 0:
            posts = [
                ('how-to-explore', 'چگونه پست‌های خود را به اکسپلور اینستاگرام ببریم؟', 'راهنمای جامع الگوریتم ۲۰۲۶ اینستاگرام و راه‌های افزایش تعامل پیج.', 'برای رفتن به اکسپلور نیاز به نرخ تعامل بالا در دقایق اولیه انتشار پست دارید...'),
                ('buy-follower-guide', 'چرا خرید فالوور واقعی باعث رشد کسب و کار می‌شود؟', 'مزایای داشتن فالوور بالای اولیه‌ برای ایجاد اعتماد در مشتریان جدید.', 'اعتماد خریدار بر اساس الگوی رفتار جمعی شکل می‌گیرد...')
            ]
            for post in posts:
                cursor.execute("INSERT INTO blog (slug, title, excerpt, content) VALUES (?, ?, ?, ?)", post)
        conn.commit()

init_db()

def generate_tracking_code():
    chars = string.ascii_uppercase + string.digits
    return 'SPF-' + ''.join(random.choices(chars, k=8))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- قالب اصلی سایت (طراحی ایران‌فالوور + منوی ۳ خطی) ---
SITE_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>سپهر فالوور | خرید فالوور، لایک و ویو اینستاگرام (طرح اصلی)</title>
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #e6123f;
            --primary-dark: #b80a2f;
            --secondary: #008eb2;
            --dark: #1f2937;
            --light-bg: #f8fafc;
            --border: #e2e8f0;
            --text-muted: #64748b;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Vazirmatn', sans-serif; }
        body { background: var(--light-bg); color: var(--dark); line-height: 1.6; padding-bottom: 60px; }

        /* هدر و منوی بالا */
        header { background: #ffffff; border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
        .top-notice { background: linear-gradient(90deg, #e6123f, #ff4b72); color: #fff; text-align: center; padding: 6px; font-size: 0.85rem; font-weight: bold; }
        .nav-container { max-width: 1200px; margin: auto; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.6rem; font-weight: 900; color: var(--primary); text-decoration: none; display: flex; align-items: center; gap: 8px; }
        
        .desktop-menu { display: flex; gap: 20px; list-style: none; }
        .desktop-menu a { text-decoration: none; color: var(--dark); font-weight: 600; font-size: 0.95rem; transition: 0.2s; }
        .desktop-menu a:hover { color: var(--primary); }
        
        /* منوی کشویی ۳ خطی همبرگری (موبایل) */
        .hamburger-btn { display: none; background: none; border: none; font-size: 1.5rem; color: var(--dark); cursor: pointer; }
        .mobile-drawer { position: fixed; top: 0; right: -280px; width: 280px; height: 100%; background: #fff; z-index: 2000; box-shadow: -5px 0 25px rgba(0,0,0,0.15); transition: 0.3s ease; padding: 20px; }
        .mobile-drawer.active { right: 0; }
        .overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1999; }
        .overlay.active { display: block; }
        .drawer-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; }
        .drawer-menu { list-style: none; }
        .drawer-menu li { margin-bottom: 15px; }
        .drawer-menu a { text-decoration: none; color: var(--dark); font-weight: 700; font-size: 1rem; display: flex; align-items: center; gap: 10px; }

        /* هیرو بنر */
        .hero-section { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #fff; text-align: center; padding: 50px 20px; border-radius: 0 0 24px 24px; }
        .hero-section h1 { font-size: 2.2rem; margin-bottom: 10px; color: #fff; font-weight: 900; }
        .hero-section p { font-size: 1.1rem; color: #94a3b8; max-width: 600px; margin: auto; }

        /* تب‌های دسته‌بندی خدمات (طرح ایران‌فالوور) */
        .container { max-width: 1200px; margin: 30px auto; padding: 0 15px; }
        .tabs-header { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-bottom: 30px; }
        .tab-btn { background: #fff; border: 1px solid var(--border); padding: 12px 22px; border-radius: 50px; font-weight: 700; cursor: pointer; transition: all 0.25s; color: var(--dark); font-size: 0.95rem; }
        .tab-btn.active, .tab-btn:hover { background: var(--primary); color: #fff; border-color: var(--primary); box-shadow: 0 4px 15px rgba(230,18,63,0.3); }

        /* کارت‌های محصولات */
        .packages-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 20px; }
        .pkg-card { background: #fff; border-radius: 16px; border: 1px solid var(--border); padding: 22px; position: relative; display: flex; flex-direction: column; justify-content: space-between; transition: 0.3s; }
        .pkg-card:hover { transform: translateY(-6px); box-shadow: 0 12px 25px rgba(0,0,0,0.08); border-color: var(--primary); }
        .pkg-badge { position: absolute; top: 12px; left: 12px; background: #fff1f2; color: var(--primary); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 800; }
        .pkg-title { font-size: 1.15rem; font-weight: 800; margin-top: 15px; margin-bottom: 12px; }
        .pkg-features { list-style: none; color: var(--text-muted); font-size: 0.88rem; margin-bottom: 20px; }
        .pkg-features li { margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        .pkg-features li i { color: #10b981; }
        .price-box { text-align: left; margin-bottom: 15px; }
        .old-price { font-size: 0.85rem; color: #94a3b8; text-decoration: line-through; }
        .main-price { font-size: 1.35rem; font-weight: 900; color: var(--dark); }
        .btn-order { background: var(--primary); color: #fff; border: none; padding: 12px; border-radius: 10px; font-weight: 800; width: 100%; cursor: pointer; transition: 0.2s; text-align: center; }
        .btn-order:hover { background: var(--primary-dark); }

        /* بخش مقالات و وبلاگ */
        .blog-section { margin-top: 60px; }
        .section-heading { font-size: 1.5rem; font-weight: 900; margin-bottom: 20px; border-right: 4px solid var(--primary); padding-right: 12px; }
        .blog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .blog-card { background: #fff; border-radius: 14px; border: 1px solid var(--border); padding: 18px; }
        .blog-card h3 { font-size: 1.05rem; margin-bottom: 8px; }
        .blog-card p { font-size: 0.88rem; color: var(--text-muted); margin-bottom: 12px; }

        /* مودال سفارش */
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 3000; align-items: center; justify-content: center; padding: 15px; }
        .modal-body { background: #fff; border-radius: 16px; padding: 25px; width: 100%; max-width: 440px; position: relative; }
        .modal-close { position: absolute; top: 15px; left: 15px; cursor: pointer; font-size: 1.2rem; }
        .form-control { width: 100%; padding: 12px; border: 1px solid var(--border); border-radius: 8px; margin-top: 6px; margin-bottom: 14px; font-size: 0.95rem; }

        @media (max-width: 768px) {
            .desktop-menu { display: none; }
            .hamburger-btn { display: block; }
        }
    </style>
</head>
<body>

    <!-- کشوی همبرگری موبایل -->
    <div class="overlay" id="overlay" onclick="toggleMenu()"></div>
    <div class="mobile-drawer" id="drawer">
        <div class="drawer-header">
            <span style="font-weight: 900; color: var(--primary);">منوی اصلی</span>
            <i class="fa fa-times" onclick="toggleMenu()" style="cursor: pointer;"></i>
        </div>
        <ul class="drawer-menu">
            <li><a href="/"><i class="fa fa-home"></i> صفحه اصلی</a></li>
            <li><a href="/track"><i class="fa fa-search"></i> پیگیری سفارش</a></li>
            <li><a href="#services"><i class="fa fa-shopping-bag"></i> تعرفه‌ها و خدمات</a></li>
            <li><a href="#blog"><i class="fa fa-blog"></i> وبلاگ و آموزش</a></li>
            <li><a href="/admin/login"><i class="fa fa-user-shield"></i> ورود مدیر</a></li>
        </ul>
    </div>

    <header>
        <div class="top-notice">⚡ سفارش‌ها به‌صورت ۲۴ ساعته و کاملاً اتوماتیک تحویل داده می‌شوند</div>
        <div class="nav-container">
            <button class="hamburger-btn" onclick="toggleMenu()"><i class="fa fa-bars"></i></button>
            <a href="/" class="logo"><i class="fa-solid fa-bolt"></i> سپهر فالوور</a>
            <ul class="desktop-menu">
                <li><a href="/">صفحه اصلی</a></li>
                <li><a href="/track">پیگیری سفارش</a></li>
                <li><a href="#services">خدمات</a></li>
                <li><a href="#blog">وبلاگ</a></li>
            </ul>
        </div>
    </header>

    <div class="hero-section">
        <h1>ارتقای هوشمندانه پیج اینستاگرام</h1>
        <p>خرید فالوور واقعی، لایک ارگانیک و ویو آنی با تضمین جبران ریزش و قیمت رقابتی</p>
    </div>

    <div class="container" id="services">
        <!-- تب‌های دسته‌بندی مشابه ایران‌فالوور -->
        <div class="tabs-header">
            <button class="tab-btn active" onclick="filterTab('all')">🔥 همه خدمات</button>
            <button class="tab-btn" onclick="filterTab('follower_ir')">👥 فالوور واقعی</button>
            <button class="tab-btn" onclick="filterTab('follower_cheap')">⚡ فالوور ارزان</button>
            <button class="tab-btn" onclick="filterTab('like')">❤️ لایک اکسپلور</button>
            <button class="tab-btn" onclick="filterTab('view')">👁️ ویو و ریلز</button>
            <button class="tab-btn" onclick="filterTab('comment')">💬 کامنت سفارشی</button>
        </div>

        <div class="packages-grid">
            {% for pkg in packages %}
            <div class="pkg-card" data-category="{{ pkg.category }}">
                {% if pkg.badge %}<span class="pkg-badge">{{ pkg.badge }}</span>{% endif %}
                <div class="pkg-title">{{ pkg.title }}</div>
                <ul class="pkg-features">
                    {% for feat in pkg.features.split('|') %}
                    <li><i class="fa fa-check-circle"></i> {{ feat.strip() }}</li>
                    {% endfor %}
                </ul>
                <div class="price-box">
                    {% if pkg.old_price %}
                    <div class="old-price">{{ "{:,}".format(pkg.old_price) }} تومان</div>
                    {% endif %}
                    <div class="main-price">{{ "{:,}".format(pkg.price) }} <span>تومان</span></div>
                </div>
                <button class="btn-order" onclick="openModal('{{ pkg.id }}', '{{ pkg.title }}', '{{ pkg.price }}')">ثبت سفارش آنی</button>
            </div>
            {% endfor %}
        </div>

        <!-- بخش وبلاگ -->
        <div class="blog-section" id="blog">
            <h2 class="section-heading">آخرین مقالات و آموزش‌ها</h2>
            <div class="blog-grid">
                {% for post in blog_posts %}
                <div class="blog-card">
                    <h3>{{ post.title }}</h3>
                    <p>{{ post.excerpt }}</p>
                    <a href="#" style="color: var(--primary); font-weight: bold; text-decoration: none; font-size: 0.85rem;">ادامه مطلب &larr;</a>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- مودال سفارش -->
    <div class="modal" id="orderModal">
        <div class="modal-body">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <h3 id="modalTitle" style="margin-bottom: 5px;"></h3>
            <p id="modalPrice" style="color: var(--primary); font-weight: 800; margin-bottom: 15px;"></p>
            <form action="/order" method="POST">
                <input type="hidden" name="package_id" id="modalPkgId">
                <label style="font-size: 0.85rem; font-weight: 700;">آیدی اینستاگرام یا لینک پست:</label>
                <input type="text" name="target" class="form-control" placeholder="مثلا sepehr_follower@" required>
                
                <label style="font-size: 0.85rem; font-weight: 700;">شماره موبایل (جهت دریافت کد پیگیری):</label>
                <input type="tel" name="phone" class="form-control" placeholder="09123456789" required>
                
                <button type="submit" class="btn-order">پرداخت و ثبت نهایی</button>
            </form>
        </div>
    </div>

    <script>
        function toggleMenu() {
            document.getElementById('drawer').classList.toggle('active');
            document.getElementById('overlay').classList.toggle('active');
        }

        function filterTab(cat) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            document.querySelectorAll('.pkg-card').forEach(card => {
                if(cat === 'all' || card.getAttribute('data-category') === cat) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function openModal(id, title, price) {
            document.getElementById('modalPkgId').value = id;
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalPrice').innerText = Number(price).toLocaleString('fa-IR') + ' تومان';
            document.getElementById('orderModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('orderModal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

# --- مسیرها (Routes) ---

@app.route('/')
def index():
    with get_db() as conn:
        pkgs = conn.execute("SELECT * FROM packages").fetchall()
        posts = conn.execute("SELECT * FROM blog ORDER BY id DESC").fetchall()
    return render_template_string(SITE_TEMPLATE, packages=pkgs, blog_posts=posts)

@app.route('/order', methods=['POST'])
def place_order():
    pkg_id = request.form.get('package_id')
    target = request.form.get('target', '').strip()
    phone = request.form.get('phone', '').strip()
    
    with get_db() as conn:
        pkg = conn.execute("SELECT * FROM packages WHERE id = ?", (pkg_id,)).fetchone()
        if not pkg:
            return "پکیج انتخاب شده یافت نشد", 404
        
        tracking = generate_tracking_code()
        conn.execute('''
            INSERT INTO orders (tracking_code, package_id, package_title, category, target_input, phone, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
        ''', (tracking, pkg['id'], pkg['title'], pkg['category'], target, phone, pkg['price']))
        conn.commit()

    return f"""
    <div style="text-align: center; padding: 50px; font-family: sans-serif; direction: rtl;">
        <h2 style="color: #10b981;">✅ سفارش شما با موفقیت ثبت شد</h2>
        <p style="margin: 15px 0;">کد پیگیری اختصاصی: <b style="color: #e6123f; font-size: 1.2rem;">{tracking}</b></p>
        <a href="/track" style="background: #e6123f; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none;">پیگیری وضعیت سفارش</a>
    </div>
    """

@app.route('/track', methods=['GET', 'POST'])
def track():
    order = None
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        with get_db() as conn:
            order = conn.execute("SELECT * FROM orders WHERE tracking_code = ?", (code,)).fetchone()
            
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>پیگیری سفارش | سپهر فالوور</title>
        <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
        <style>
            * { font-family: 'Vazirmatn', sans-serif; box-sizing: border-box; }
            body { background: #f8fafc; padding: 40px 15px; }
            .box { max-width: 480px; margin: auto; background: #fff; padding: 25px; border-radius: 16px; border: 1px solid #e2e8f0; }
            input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; margin: 10px 0 15px; }
            button { width: 100%; background: #e6123f; color: #fff; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🔍 استعلام پیگیری سفارش</h2>
            <form method="POST">
                <label>کد پیگیری (مانند SPF-XXXXX):</label>
                <input type="text" name="code" required>
                <button type="submit">بررسی وضعیت</button>
            </form>
            {% if order %}
            <div style="margin-top: 20px; padding: 15px; background: #f1f5f9; border-radius: 8px;">
                <p><b>محصول:</b> {{ order.package_title }}</p>
                <p><b>هدف:</b> {{ order.target_input }}</p>
                <p><b>وضعیت:</b> <span style="color: green; font-weight: bold;">{{ order.status }}</span></p>
            </div>
            {% endif %}
            <p style="text-align: center; margin-top: 15px;"><a href="/" style="color: #e6123f; text-decoration: none;">بازگشت به خانه</a></p>
        </div>
    </body>
    </html>
    """, order=order)

# --- پنل مدیریت (Admin) ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('user')
        passwd = request.form.get('pass')
        if user == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, passwd):
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('نام کاربری یا کلمه عبور نادرست است.')
    return """
    <div style="max-width:320px; margin:80px auto; font-family:sans-serif; direction:rtl;">
        <h2>ورود به مدیریت</h2>
        <form method="post">
            <input name="user" placeholder="نام کاربری" style="width:100%; padding:8px; margin-bottom:10px;"><br>
            <input type="password" name="pass" placeholder="رمز عبور" style="width:100%; padding:8px; margin-bottom:10px;"><br>
            <button style="width:100%; padding:10px; background:#e6123f; color:#fff; border:none;">ورود</button>
        </form>
    </div>
    """

@app.route('/admin')
@admin_required
def admin_dashboard():
    with get_db() as conn:
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        total_income = conn.execute("SELECT SUM(amount) FROM orders WHERE status='completed'").fetchone()[0] or 0
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>پنل مدیریت سپهر فالوور</title>
        <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
        <style>
            * { font-family: 'Vazirmatn', sans-serif; }
            body { background: #f8fafc; padding: 20px; }
            table { width: 100%; border-collapse: collapse; background: #fff; margin-top: 20px; }
            th, td { border: 1px solid #cbd5e1; padding: 10px; text-align: right; }
            th { background: #f1f5f9; }
        </style>
    </head>
    <body>
        <h1>پنل مدیریت سفارشات</h1>
        <p>درآمد کل: <b>{{ "{:,}".format(income) }} تومان</b></p>
        <table>
            <tr>
                <th>کد پیگیری</th>
                <th>عنوان پکیج</th>
                <th>هدف (آیدی/لینک)</th>
                <th>موبایل</th>
                <th>مبلغ</th>
                <th>وضعیت</th>
                <th>عملیات</th>
            </tr>
            {% for o in orders %}
            <tr>
                <td>{{ o.tracking_code }}</td>
                <td>{{ o.package_title }}</td>
                <td>{{ o.target_input }}</td>
                <td>{{ o.phone }}</td>
                <td>{{ "{:,}".format(o.amount) }}</td>
                <td>{{ o.status }}</td>
                <td>
                    <a href="/admin/status/{{o.id}}/completed">تکمیل</a> | 
                    <a href="/admin/status/{{o.id}}/canceled">لغو</a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """, orders=orders, income=total_income)

@app.route('/admin/status/<int:order_id>/<status>')
@admin_required
def update_status(order_id, status):
    with get_db() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)

