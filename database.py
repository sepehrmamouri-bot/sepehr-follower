import sqlite3
from config import Config
from werkzeug.security import generate_password_hash

def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    # تنظیم حالت WAL برای جلوگیری از تداخل و کرش در پایتون‌انی‌ور
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # ۱. جدول کاربران
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            wallet INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # ۲. جدول سرویس‌ها (برای جدول خدمات)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price_per_1000 INTEGER NOT NULL,
            min_order INTEGER NOT NULL,
            max_order INTEGER NOT NULL,
            description TEXT,
            smm_service_id TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0
        );
        ''')

        # ۳. جدول پکیج‌های آماده صفحه اول
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
        );
        ''')

        # ۴. جدول سفارشات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_code TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            service_id INTEGER,
            package_id INTEGER,
            package_title TEXT,
            category TEXT,
            target_input TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            smm_order_id TEXT,
            payment_authority TEXT,
            payment_ref_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        ''')

        # ۵. تراکنش‌های مالی
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            ref_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        ''')

        # ۶. وبلاگ
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            excerpt TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # مقداردهی پیش‌فرض اولیه در صورت خالی بودن سرویس‌ها و پکیج‌ها
        cursor.execute("SELECT COUNT(*) FROM packages")
        if cursor.fetchone()[0] == 0:
            sample_pkgs = [
                ('follower_ir', '۱,۰۰۰ فالوور ایرانی واقعی VIP', 1000, 189000, 260000, 'پروفایل کامل | سرعت ارگانیک | ۳۰ روز ضمانت', 'پرفروش'),
                ('follower_cheap', '۱,۰۰۰ فالوور اقتصادی میکس', 1000, 68000, 95000, 'ارزان‌ترین نرخ | شروع سریع | بدون نیاز به رمز', 'اقتصادی'),
                ('like', '۱,۰۰۰ لایک ایرانی پست', 1000, 49000, 75000, 'سرعت بالا | اثر مثبت در ورود به اکسپلور', 'محبوب'),
                ('view', '۱۰,۰۰۰ بازدید ریلز اینستاگرام', 10000, 45000, 70000, 'ارسال آنی کمتر از ۱۰ دقیقه | بدون افت', 'ویژه'),
                ('telegram', '۱,۰۰۰ عضو کانال تلگرام', 1000, 85000, 120000, 'میکسی ارزان | بدون ریزش اولیه | مناسب کانال جدید', 'جدید')
            ]
            cursor.executemany("INSERT INTO packages (category, title, quantity, price, old_price, features, badge) VALUES (?,?,?,?,?,?,?)", sample_pkgs)

        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            sample_services = [
                ('فالوور اینستاگرام', 'فالوور واقعی ایرانی سرور ۱', 189000, 500, 50000, 'سرعت ۱ تا ۵ کا در روز با کیفیت عالی', '101'),
                ('فالوور اینستاگرام', 'فالوور فیک ارزان سرور ۳', 68000, 100, 100000, 'ارزان‌ترین سرور بدون ضمانت', '102'),
                ('لایک اینستاگرام', 'لایک ایرانی بدون افت', 49000, 50, 20000, 'تحویل در کمتر از ۱۵ دقیقه', '201'),
                ('ویو و بازدید', 'ویو ریلز اینستاگرام سرعت بالا', 4500, 1000, 1000000, 'مناسب پیج‌های اکسپلوری', '301'),
                ('تلگرام', 'ممبر فیک کانال تلگرام', 85000, 100, 50000, 'پایدار و باکیفیت', '401')
            ]
            cursor.executemany("INSERT INTO services (category, name, price_per_1000, min_order, max_order, description, smm_service_id) VALUES (?,?,?,?,?,?,?)", sample_services)

        cursor.execute("SELECT COUNT(*) FROM blog")
        if cursor.fetchone()[0] == 0:
            sample_blogs = [
                ('increase-engagement-2026', 'چگونه در سال ۲۰۲۶ ریلزهای میلیونی بسازیم؟', 'نکات طلایی برای ورود به اکسپلور و تعامل بالا با الگوریتم جدید.', 'در الگوریتم جدید، نرخ سیو و شیر ویدیو ریلز مهم‌ترین فاکتور ورود به صفحه اکسپلور است...'),
                ('buy-instagram-followers-guide', 'راهنمای خرید اصولی فالوور بدون شادوبن شدن', 'چرا نباید فالوور ارزان را با سرعت بالا به پیج نوپا تزریق کرد؟', 'تزریق ناگهانی فالوور می‌تواند باعث برانگیخته شدن هشدارهای امنیتی اینستاگرام شود...')
            ]
            cursor.executemany("INSERT INTO blog (slug, title, excerpt, content) VALUES (?,?,?,?)", sample_blogs)

        conn.commit()

