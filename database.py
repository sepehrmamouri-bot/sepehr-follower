import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # جدول سرویس‌ها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        price INTEGER NOT NULL,
        min_amount INTEGER DEFAULT 100,
        max_amount INTEGER DEFAULT 50000,
        badge TEXT DEFAULT 'ویژه',
        api_id INTEGER DEFAULT 0
    )
    """)

    # جدول سفارش‌ها
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tracking_code TEXT UNIQUE NOT NULL,
        service_id INTEGER NOT NULL,
        target TEXT NOT NULL,
        phone TEXT NOT NULL,
        amount INTEGER NOT NULL,
        total_price INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_id) REFERENCES services (id)
    )
    """)

    # جدول کدهای تخفیف
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        percent INTEGER NOT NULL,
        active INTEGER DEFAULT 1
    )
    """)

    # داده‌های اولیه پیش‌فرض
    cursor.execute("SELECT COUNT(*) FROM services")
    if cursor.fetchone()[0] == 0:
        default_services = [
            ('instagram', 'فالوور ۱۰۰٪ واقعی ایرانی پاپ‌آپ', 'جذب کاملاً ارگانیک از طریق نوتیفیکیشن پیج‌های پربازدید', 38000, 500, 20000, 'پرفروش‌ترین'),
            ('instagram', 'فالوور اقتصادی بین‌المللی (ثابت)', 'سرعت ارسال بی‌نظیر مناسب استارت پیج‌های کاری', 18000, 100, 100000, 'اقتصادی'),
            ('instagram', 'لایک فوق‌سریع اکسپلوری با ایمپرشن', 'ارسال همزمان سیو و ریچ، تضمین تقویت ورود به اکسپلور', 8500, 100, 50000, 'محبوب'),
            ('telegram', 'ممبر واقعی کانال تلگرام (پروکسی اسپانسری)', 'جذب زنده کاربران فعال از طریق پروکسی‌های قدرتمند MTProto', 45000, 500, 10000, 'کیفیت طلایی'),
            ('telegram', 'ممبر فیک بدون ریزش با کیفیت', 'تکمیل زیر ۵ دقیقه جهت افزایش اعتبار اولیه کانال', 22000, 100, 50000, 'ارزان'),
            ('youtube', 'سابسکرایبر فعال و غیرقابل حذف', 'کاملاً ایمن برای مانیتایز کانال با ماندگاری مادام‌العمر', 130000, 50, 5000, 'تضمینی')
        ]
        cursor.executemany("""
            INSERT INTO services (category, title, description, price, min_amount, max_amount, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, default_services)

        cursor.execute("INSERT INTO coupons (code, percent) VALUES ('SEPEHR2026', 20)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
    print("Database updated and initialized successfully!")

