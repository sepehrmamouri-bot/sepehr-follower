import os
import sqlite3
from flask import Flask, render_template_string, request, jsonify, Response

app = Flask(__name__)
DB_PATH = 'database.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                category TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                link TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # دیتای پیش‌فرض خدمات
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM services')
        if cur.fetchone()[0] == 0:
            services = [
                ('فالوور واقعی و فعال ایرانی (بدون ریزش)', 45000, 'فالوور'),
                ('فالوور ارزان و پرسرعت (میکس جهانی)', 18000, 'فالوور'),
                ('لایک واقعی پست اینستاگرام (آنی)', 8000, 'لایک'),
                ('ویو / بازدید ویدیو و ریلز اینستاگرام', 3000, 'ویو'),
                ('ممبر واقعی کانال تلگرام', 35000, 'تلگرام')
            ]
            conn.executemany('INSERT INTO services (name, price, category) VALUES (?, ?, ?)', services)
            conn.commit()

init_db()

# تمپلیت کامل با رعایت متاتگ‌های فنی سئو، Schema JSON-LD و رابط کاربری شیشه‌ای
INDEX_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- سئو: عنوان و دیسکریپشن هدفمند برای رتبه ۱ -->
    <title>پنل خرید فالوور واقعی و ارزان اینستاگرام | تحویل آنی و تضمینی</title>
    <meta name="description" content="ارزان‌ترین و معتبرترین پنل فروش فالوور، لایک، ویو ریلز و ممبر تلگرام بدون پسورد با تحویل فوری، گارانتی عدم ریزش و پشتیبانی ۲۴ ساعته.">
    <meta name="keywords" content="خرید فالوور, پنل فالوور ارزان, خرید فالوور واقعی, پنل ممبر تلگرام, خرید لایک اینستاگرام">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://yourdomain.com/">

    <!-- تگ‌های شبکه‌های اجتماعی Open Graph -->
    <meta property="og:locale" content="fa_IR">
    <meta property="og:type" content="website">
    <meta property="og:title" content="پنل هوشمند خرید فالوور و لایک واقعی اینستاگرام">
    <meta property="og:description" content="افزایش تضمینی فالوور و ورود به اکسپلور با نازل‌ترین تعرفه بازار ایران.">

    <!-- Schema.org برای ثبت ستاره و سوالات متداول در گوگل -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Product",
          "name": "پنل خرید فالوور و خدمات شبکه‌های اجتماعی",
          "description": "فروش فالوور واقعی، لایک و ویو اینستاگرام با تحویل آنی و ارزان‌ترین قیمت",
          "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "2410"
          },
          "offers": {
            "@type": "AggregateOffer",
            "priceCurrency": "IRR",
            "lowPrice": "3000",
            "highPrice": "45000",
            "offerCount": "5"
          }
        },
        {
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "آیا برای خرید فالوور نیاز به ارائه پسورد پیج است؟",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "خیر، تمامی خدمات بدون نیاز به پسورد و تنها با وارد کردن آیدی یا لینک عمومی پیج انجام می‌شود."
              }
            },
            {
              "@type": "Question",
              "name": "سفارشات چقدر زمان می‌برند تا تکمیل شوند؟",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "سیستم به صورت تمام اتوماتیک عمل می‌کند و سفارشات ظرف کمتر از ۱ تا ۵ دقیقه آغاز می‌شوند."
              }
            }
          ]
        }
      ]
    }
    </script>

    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent: #ec4899;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: rgba(255, 255, 255, 0.1);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
        body {
            background: radial-gradient(circle at top, #1e1b4b 0%, var(--bg-color) 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .container { width: 100%; max-width: 650px; margin: auto; }
        header { text-align: center; margin-bottom: 25px; }
        header h1 { font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #a855f7, var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        header p { color: var(--text-muted); font-size: 0.95rem; }
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 25 0%, var(--bg-color) 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .container { width: 100%; max-width: 650px; margin: auto; }
        header { text-align: center; margin-bottom: 25px; }
        header h1 { font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #a855f7, var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        header p { color: var(--text-muted); font-size: 0.95rem; }
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 25rem; }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 1.05rem;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.92; }
        .faq-section { margin-top: 15px; }
        .faq-item { margin-bottom: 12px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px; }
        .faq-item h3 { font-size: 1rem; color: #e2e8f0; margin-bottom: 4px; }
        .faq-item p { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>سامانه هوشمند فروش فالوور و لایک</h1>
            <p>سفارش آنی بدون واسطه با سریع‌ترین الگوریتم تحویل سرور</p>
        </header>

        <main class="card">
            <form id="orderForm">
                <div class="form-group">
                    <label>نوع سرویس</label>
                    <select id="serviceSelect" onchange="calculatePrice()">
                        {% for s in services %}
                            <option value="{{ s.name }}" data-price="{{ s.price }}">{{ s.name }} - {{ "{:,}".format(s.price) }} تومان / ۱۰۰۰ عدد</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="form-group">
                    <label>لینک یا آیدی پیج (بدون نیاز به پسورد)</label>
                    <input type="text" id="targetLink" placeholder="مثال: mypage_id" required>
                </div>

                <div class="form-group">
                    <label>تعداد سفارش (حداقل ۱۰۰)</label>
                    <input type="number" id="targetQuantity" value="1000" min="100" step="100" oninput="calculatePrice()" required>
                </div>

                <div class="price-box">
                    مبلغ نهایی: <span class="price-val" id="finalPrice">0</span> تومان
                </div>

                <button type="submit" id="submitBtn">ثبت فوری سفارش</button>
            </form>
        </main>

        <section class="card faq-section">
            <h2 style="font-size: 1.15rem; margin-bottom: 12px;">سوالات متداول کاربران (FAQ)</h2>
            <article class="faq-item">
                <h3>آیا پیج مسدود یا دچار مشکل می‌شود؟</h3>
                <p>تمامی سفارشات بر پایه استاندارد و پروتکل‌های رسمی ارسال شده و هیچ خطری برای صفحه شما نخواهد داشت.</p>
            </article>
            <article class="faq-item">
                <h3>چرا این پنل رتبه یک است؟</h3>
                <p>تحویل آنی ۲۴ ساعته، پایین‌ترین تعرفه بدون دلال و پشتیبانی فعال ما وجه تمایز ماست.</p>
            </article>
        </section>
    </div>

    <script>
        function calculatePrice() {
            const select = document.getElementById('serviceSelect');
            const pricePer1k = parseInt(select.options[select.selectedIndex].getAttribute('data-price'));
            const qty = parseInt(document.getElementById('targetQuantity').value) || 0;
            const total = Math.round((pricePer1k * qty) / 1000);
            document.getElementById('finalPrice').innerText = total.toLocaleString('fa-IR');
        }

        calculatePrice();

        document.getElementById('orderForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            btn.disabled = true;
            btn.innerText = 'در حال ثبت...';

            const payload = {
                service_name: document.getElementById('serviceSelect').value,
                link: document.getElementById('targetLink').value,
                quantity: document.getElementById('targetQuantity').value
            };

            const res = await fetch('/api/order', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            alert(data.message);
            btn.disabled = false;
            btn.innerText = 'ثبت فوری سفارش';
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    with get_db() as conn:
        services = conn.execute('SELECT * FROM services').fetchall()
    return render_template_string(INDEX_HTML, services=services)

@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.json
    service_name = data.get('service_name')
    link = data.get('link')
    quantity = int(data.get('quantity', 0))

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute('SELECT price FROM services WHERE name = ?', (service_name,))
        res = cur.fetchone()
        if not res:
            return jsonify({'status': 'error', 'message': 'سرویس یافت نشد'}), 400
        
        unit_price = res['price']
        total = int((unit_price * quantity) / 1000)

        conn.execute('INSERT INTO orders (service_name, link, quantity, total_price) VALUES (?, ?, ?, ?)',
                     (service_name, link, quantity, total))
        conn.commit()

    return jsonify({'status': 'success', 'message': f'سفارش شما با شماره ثبت شد. مبلغ: {total:,} تومان'})

# این ۲ مسیر برای تایید رسمی ربات گوگل الزامی هستند:
@app.route('/robots.txt')
def robots():
    content = "User-agent: *\nAllow: /\nSitemap: https://yourdomain.com/sitemap.xml"
    return Response(content, mimetype="text/plain")

@app.route('/sitemap.xml')
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
       <url>
          <loc>https://yourdomain.com/</loc>
          <priority>1.0</priority>
          <changefreq>daily</changefreq>
       </url>
    </urlset>"""
    return Response(xml, mimetype="application/xml")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

