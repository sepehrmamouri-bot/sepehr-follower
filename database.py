import sqlite3
import os

DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

get_db_connection = get_db

def init_database():
    conn = get_db()
    cursor = conn.cursor()

    # ۱. جدول پکیج‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_type TEXT NOT NULL,
        title TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price INTEGER NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # ۲. جدول سفارشات
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_code TEXT UNIQUE NOT NULL,
        service_title TEXT NOT NULL,
        target_link TEXT NOT NULL,
        phone TEXT,
        amount INTEGER NOT NULL,
        status TEXT DEFAULT 'در انتظار پرداخت',
        payment_ref TEXT,
        api_order_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # ۳. جدول تخفیف‌ها
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_percent INTEGER NOT NULL,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # ۴. جدول سئو و مقالات وبلاگ
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        meta_description TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'اینستاگرام',
        reading_time INTEGER DEFAULT 5,
        views INTEGER DEFAULT 0,
        published_date TEXT DEFAULT '۱۴۰۳/۰۶/۲۷',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # افزودن پکیج‌های پیش‌فرض در صورت خالی بودن
    cursor.execute("SELECT COUNT(*) FROM packages")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO packages (service_type, title, quantity, price, description)
        VALUES (?, ?, ?, ?, ?)
        ''', [
            ('follower', '۱,۰۰۰ فالوور ایرانی واقعی', 1000, 39000, 'کیفیت بالا، ارسال سریع با کمترین ریزش'),
            ('follower', '۵,۰۰۰ فالوور ایرانی ویژه', 5000, 185000, 'دارای ضمانت جبران ریزش و سرعت بالا'),
            ('like', '۲,۰۰۰ لایک پست و ریلز', 2000, 19000, 'افزایش تعامل و رفتن به اکسپلور اینستاگرام'),
            ('member', '۱,۰۰۰ ممبر کانال تلگرام', 1000, 35000, 'ممبرهای بدون ریزش با کیفیت تضمینی')
        ])

    # افزودن مقالات سئویی مرجع در صورت خالی بودن
    cursor.execute("SELECT COUNT(*) FROM articles")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO articles (title, slug, meta_description, content, category, reading_time, published_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            (
                'الگوریتم جدید اینستاگرام ۲۰۲۶ و ترفندهای قطعی ورود به اکسپلور',
                'instagram-explore-algorithm-2026',
                'کامل‌ترین راهنمای ورود به اکسپلور اینستاگرام در سال ۲۰۲۶ بر اساس آخرین تغییرات الگوریتم هوش مصنوعی متا.',
                '''<h2>چگونه در سال ۲۰۲۶ پست‌هایمان را به اکسپلور ببریم؟</h2>
                <p>الگوریتم جدید اینستاگرام بیش از هر زمان دیگری بر پایه رفتار مخاطب در ثانیه‌های اول طراحی شده است. نرخ نگهداری تماشاچی (Watch Time) در ریلزها و نسبت ذخیره (Save) و اشتراک‌گذاری (Share) دو فاکتور حیاتی برای سیستم پیشنهاددهنده هوش مصنوعی اینستاگرام هستند.</p>
                <h3>۳ گام اساسی برای سیگنال مثبت به الگوریتم:</h3>
                <ul>
                    <li><b>استارت قدرتمند (۳ ثانیه اول):</b> بدون مقدمه‌چینی اضافه، قلاب ذهنی (Hook) را در ۳ ثانیه اول ویدیو اجرا کنید.</li>
                    <li><b>نرخ تعامل اولیه:</b> استفاده از پکیج‌های افزایش لایک و بازدید در ساعت اول انتشار پست، موتور اکسپلور را روشن می‌کند.</li>
                    <li><b>تداوم و منظم بودن:</b> حفظ ریتم ثابت انتشار هفتگی باعث دریافت اولویت در فید فالوورها می‌شود.</li>
                </ul>''',
                'آموزش اینستاگرام',
                6,
                '۱۴۰۳/۰۶/۲۷'
            ),
            (
                'چرا خرید فالوور و لایک واقعی برای رشد کسب‌وکارهای آنلاین ضروری است؟',
                'why-buy-followers-for-business-growth',
                'بررسی روانشناسی سوشال پروف (Social Proof) و تاثیر مستقیم تعداد دنبال‌کننده در افزایش فروش پیج‌های تجاری.',
                '''<h2>اصل تایید اجتماعی یا Social Proof چیست؟</h2>
                <p>وقتی یک مشتری جدید وارد پیج فروشگاهی شما می‌شود، اولین المانی که قبل از مطالعه توضیحات کالا بررسی می‌کند، میزان محبوبیت و تعداد دنبال‌کنندگان شماست. اگر یک پیج بهترین محصول دنیا را با قیمت مناسب داشته باشد اما ۲۰۰ فالوور داشته باشد، ذهن مخاطب احساس ریسک و عدم اعتماد می‌کند.</p>
                <h3>مزایای مستقیم داشتن پایه فالوور قوی:</h3>
                <ul>
                    <li>افزایش ۶۰ درصدی نرخ تبدیل مخاطب به خریدار واقعی</li>
                    <li>جلب اعتماد سریع در دایرکت و ثبت سفارش</li>
                    <li>کاهش هزینه تبلیغات اینفلوئنسری و جذب با بازدهی دوبرابر</li>
                </ul>''',
                'کسب‌وکار اینترنتی',
                5,
                '۱۴۰۳/۰۶/۲۷'
            ),
            (
                'راهنمای افزایش ممبر واقعی تلگرام و افزایش بازدید کانال',
                'telegram-channel-growth-guide',
                'روش‌های نوین و اصولی رشد کانال تلگرام، جذب ممبر هدفمند و استراتژی‌های سین زدن پست‌ها.',
                '''<h2>چطور یک کانال تلگرامی پردرآمد بسازیم؟</h2>
                <p>تلگرام یکی از پربازده‌ترین بسترهای فروشگاهی در ایران است. برای اینکه کانال شما بتواند توجه مخاطب را جلب کند، نسبت بین تعداد ممبرها و سین (View) پست‌ها باید طبیعی و متناسب باشد.</p>
                <p>استفاده از ممبرهای باکیفیت به همراه بازدید روزانه برای آخرین پست‌ها، پرستیژ و رتبه کانال شما را در سرچ تلگرام ارتقا می‌دهد.</p>''',
                'رشد تلگرام',
                4,
                '۱۴۰۳/۰۶/۲۷'
            )
        ])

    conn.commit()
    conn.close()

def init_db():
    init_database()

if __name__ == '__main__':
    init_database()
    print("Database & SEO Articles initialized successfully.")

