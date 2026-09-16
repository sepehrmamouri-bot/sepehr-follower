# -*- coding: utf-8 -*-
"""
پروژه جامع سپهر فالوور (Sepehr Follower Pro)
ترکیب هویت بصری دیجی‌کالا با قیف فروش ایران فالوور
مجهز به فروشگاه، پیگیری مرحله‌ای سفارش، پنل مدیریت، وبلاگ و سئو
"""

import os
import sqlite3
import random
import string
import datetime
import requests
from functools import wraps
from flask import (
    Flask, request, session, redirect, url_for,
    render_template_string, Response, jsonify, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sepehr_follower_super_secret_key_2026")
DB_FILE = "sepehr_follower.db"

# تنظیمات اصلی
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123456")
ZARINPAL_MERCHANT = os.environ.get("ZARINPAL_MERCHANT", "")
SITE_URL = "https://sepehrmamouri-bot.pythonanywhere.com"

# --- دیتابیس ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        # جدول پکیج‌ها
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
        # جدول سفارش‌ها
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
                status TEXT DEFAULT 'pending', -- pending, processing, completed, canceled
                ref_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # جدول وبلاگ
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

        # افزودن داده‌های اولیه در صورت خالی بودن
        cursor.execute("SELECT COUNT(*) FROM packages")
        if cursor.fetchone()[0] == 0:
            initial_packages = [
                ('follower_ir', '۱,۰۰۰ فالوور ایرانی واقعی', 1000, 189000, 260000, 'پروفایل کامل ایرانی|سرعت ارسال طبیعی|ضمانت جبران ریزش ۳۰ روزه|بدون نیاز به پسورد', 'شگفت‌انگیز', 1),
                ('follower_ir', '۲,۵۰۰ فالوور ایرانی باکیفیت', 2500, 445000, 590000, 'کاربران فعال اینستاگرام|ورود به اکسپلور|پشتیبانی اختصاصی|بدون پسورد', 'پرفروش', 0),
                ('follower_ir', '۵,۰۰۰ فالوور ایرانی طلایی', 5000, 850000, 1150000, 'کیفیت تضمینی VIP|مناسب پیج‌های تجاری|بونوس هدیه لایک|پشتیبانی ۲۴ ساعته', 'پیشنهاد ویژه', 1),
                ('follower_cheap', '۱,۰۰۰ فالوور اقتصادی', 1000, 68000, 95000, 'استارت فوری و سریع|ارزان‌ترین نرخ بازار|مناسب بالا بردن اعتبار پیج', 'ارزان', 0),
                ('follower_cheap', '۵,۰۰۰ فالوور میکس اقتصادی', 5000, 310000, 430000, 'تحویل سریع اتوماتیک|بدون نیاز به پسورد|کیفیت استاندارد', 'اقتصادی', 0),
                ('like', '۱,۰۰۰ لایک ایرانی واقعی', 1000, 49000, 75000, 'پروفایل‌های ایرانی|افزایش ایمپرشن و ریچ|شروع کمتر از ۵ دقیقه', 'محبوب', 1),
                ('like', '۵,۰۰۰ لایک ارگانیک', 5000, 215000, 290000, 'پخش تدریجی و طبیعی|کمک به رفتن به اکسپلور|پشتیبانی سریع', 'ویژه اکسپلور', 0),
                ('view', '۵,۰۰۰ بازدید ویدیو / ریلز', 5000, 24000, 39000, 'افزایش بازدید ویدیو و Reels|استارت آنی زیر ۲ دقیقه|بسیار ارزان', 'فوری', 0),
                ('view', '۲۰,۰۰۰ ویو میلیونی ریلز', 20000, 89000, 140000, 'پوشش الگوریتم ریلز اینستاگرام|تحویل آنی خودکار|تضمین کیفیت', 'شگفت‌انگیز', 1),
                ('comment', '۱۰۰ کامنت مرتبط فارسی', 100, 79000, 110000, 'متن‌های مثبت و دلخواه|پروفایل‌های معتبر فارسی|افزایش چشمگیر تعامل', 'تخصصی', 0)
            ]
            for p in initial_packages:
                cursor.execute(
                    "INSERT INTO packages (category, title, quantity, price, old_price, features, badge, is_special) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    p
                )

        cursor.execute("SELECT COUNT(*) FROM blog_posts")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO blog_posts (slug, title, excerpt, content) VALUES
                ('how-to-grow-instagram', 'راهنمای جامع رشد پیج اینستاگرام در سال ۲۰۲۶', 'چگونه با ترکیب خرید هدفمند فالوور و الگوریتم ریلز فروش خود را ۱۰ برابر کنیم؟', '<p>رشد در اینستاگرام نیازمند ایجاد اعتماد و جذب تعامل اولیه است. خرید فالوور باکیفیت به همراه لایک و ویو متناسب باعث فعال شدن الگوریتم اکسپلور می‌شود...</p>'),
                ('why-sepehrfollower', 'چرا سپهر فالوور بهترین انتخاب برای خدمات شبکه‌های اجتماعی است؟', 'بررسی مزایای تحویل آنی، ضمانت ریزش و پرداخت امن بدون نیاز به رمز عبور پیج.', '<p>در سپهر فالوور تمام سفارش‌ها به صورت اتوماتیک و بدون دریافت کلمه عبور پیج انجام می‌پذیرد...</p>')
            ''')
        conn.commit()

init_db()

# --- سیستم احراز هویت ادمین ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_tracking_code():
    chars = string.ascii_uppercase + string.digits
    return "SF-" + "".join(random.choices(chars, k=6))

# --- تمپلیت اصلی دیجی‌کالایی (Digikala x IranFollower UI) ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title or 'سپهر فالوور | خرید فالوور، لایک و ویو اینستاگرام با تحویل آنی' }}</title>
    <meta name="description" content="مرجع تخصصی خرید فالوور واقعی اینستاگرام، لایک، بازدید ریلز و کامنت با تحویل فوری، بدون نیاز به رمز عبور و پشتیبانی ۲۴ ساعته">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#fff1f2',
                            100: '#ffe4e6',
                            500: '#f43f5e',
                            600: '#e11d48',
                            700: '#be123c',
                            dk: '#ef394e' // دیجی‌کالا رد
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Vazirmatn', sans-serif; background-color: #f7f7f8; }
        .dk-shadow { box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
        .dk-shadow-hover:hover { box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); }
        .tab-btn.active { background-color: #ef394e; color: #fff; border-color: #ef394e; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .modal-blur { backdrop-filter: blur(6px); }
    </style>
</head>
<body class="text-slate-800 flex flex-col min-h-screen pb-16 md:pb-0">

    <!-- نوار شگفت‌انگیز بالا -->
    <div class="bg-gradient-to-r from-red-600 via-rose-600 to-pink-600 text-white text-xs py-2 px-4 text-center font-bold flex items-center justify-center gap-2">
        <i class="fa-solid fa-fire text-yellow-300 animate-pulse"></i>
        <span>تخفیف ویژه سفارش‌های اول: تا ۴۰٪ تخفیف روی تمامی بسته‌های فالوور و لایک واقعی!</span>
    </div>

    <!-- هدر اصلی دیجی‌کالایی -->
    <header class="bg-white border-b sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
            <!-- لوگو -->
            <div class="flex items-center gap-3">
                <a href="/" class="flex items-center gap-2">
                    <span class="w-10 h-10 rounded-2xl bg-brand-dk text-white flex items-center justify-center text-xl font-black shadow-md shadow-red-200">
                        <i class="fa-brands fa-instagram"></i>
                    </span>
                    <div>
                        <div class="text-xl font-black tracking-tight text-slate-900 leading-none">سپهر<span class="text-brand-dk">فالوور</span></div>
                        <span class="text-[10px] text-slate-400 font-semibold">مرجع خدمات شبکه‌های اجتماعی</span>
                    </div>
                </a>
            </div>

            <!-- منو دسترسی دسکتاپ -->
            <nav class="hidden md:flex items-center gap-6 text-sm font-semibold text-slate-600">
                <a href="/" class="hover:text-brand-dk transition">صفحه اصلی</a>
                <a href="#services" class="hover:text-brand-dk transition">تعرفه‌ها و خدمات</a>
                <a href="#incredible" class="hover:text-brand-dk transition text-rose-600 flex items-center gap-1">
                    <i class="fa-solid fa-bolt text-xs"></i> شگفت‌انگیزها
                </a>
                <a href="/track" class="hover:text-brand-dk transition flex items-center gap-1">
                    <i class="fa-solid fa-truck-fast text-xs"></i> پیگیری سفارش
                </a>
                <a href="/blog" class="hover:text-brand-dk transition">وبلاگ آموزشی</a>
            </nav>

            <!-- دکمه پیگیری و ثبت سفارش -->
            <div class="flex items-center gap-3">
                <a href="/track" class="hidden sm:inline-flex items-center gap-2 text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 px-4 py-2.5 rounded-xl transition">
                    <i class="fa-solid fa-receipt text-slate-500"></i> پیگیری خرید
                </a>
                <a href="#services" class="bg-brand-dk hover:bg-red-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-md shadow-red-200 transition flex items-center gap-1">
                    <i class="fa-solid fa-cart-shopping"></i> خرید سریع
                </a>
            </div>
        </div>
    </header>

    <!-- بدنه صفحه -->
    <main class="flex-grow">
        {% block content %}{% endblock %}
    </main>

    <!-- مزایای اعتمادساز دیجی‌کالایی -->
    <section class="bg-white border-t py-8 mt-12">
        <div class="max-w-6xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-2xl bg-red-50 text-brand-dk flex items-center justify-center text-xl mb-2">
                    <i class="fa-solid fa-bolt"></i>
                </div>
                <h4 class="font-bold text-sm text-slate-800">تحویل آنی و خودکار</h4>
                <p class="text-xs text-slate-400 mt-1">شروع سفارش در کمتر از ۵ دقیقه</p>
            </div>
            <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-xl mb-2">
                    <i class="fa-solid fa-shield-halved"></i>
                </div>
                <h4 class="font-bold text-sm text-slate-800">ضمانت جبران ریزش</h4>
                <p class="text-xs text-slate-400 mt-1">گارانتی تعویض و جبران فالوور</p>
            </div>
            <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center text-xl mb-2">
                    <i class="fa-solid fa-lock"></i>
                </div>
                <h4 class="font-bold text-sm text-slate-800">بدون نیاز به پسورد</h4>
                <p class="text-xs text-slate-400 mt-1">فقط با وارد کردن آیدی پیج</p>
            </div>
            <div class="flex flex-col items-center">
                <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl mb-2">
                    <i class="fa-solid fa-headset"></i>
                </div>
                <h4 class="font-bold text-sm text-slate-800">پشتیبانی ۲۴ ساعته</h4>
                <p class="text-xs text-slate-400 mt-1">پاسخگویی آنلاین و تلگرامی</p>
            </div>
        </div>
    </section>

    <!-- فوتر دیجی‌کالایی -->
    <footer class="bg-slate-900 text-slate-400 text-xs pt-12 pb-20 md:pb-8 border-t border-slate-800">
        <div class="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div class="space-y-3">
                <div class="text-xl font-black text-white">سپهر<span class="text-brand-dk">فالوور</span></div>
                <p class="leading-relaxed text-slate-400 text-justify">
                    سپهر فالوور، پلتفرم تخصصی افزایش فالوور، لایک، ویو ریلز و تعامل اینستاگرام. با بیش از ۵ سال تجربه در بازاریابی شبکه‌های اجتماعی، کسب و کار شما را به اکسپلور هدایت می‌کنیم.
                </p>
            </div>
            <div>
                <h5 class="text-white font-bold text-sm mb-3">خدمات پرطرفدار</h5>
                <ul class="space-y-2">
                    <li><a href="/#follower_ir" class="hover:text-white transition">خرید فالوور ایرانی واقعی</a></li>
                    <li><a href="/#follower_cheap" class="hover:text-white transition">فالوور ارزان و فوری</a></li>
                    <li><a href="/#like" class="hover:text-white transition">خرید لایک اکسپلور</a></li>
                    <li><a href="/#view" class="hover:text-white transition">افزایش ویو ریلز میلیونی</a></li>
                </ul>
            </div>
            <div>
                <h5 class="text-white font-bold text-sm mb-3">دسترسی سریع</h5>
                <ul class="space-y-2">
                    <li><a href="/track" class="hover:text-white transition">پیگیری لحظه‌ای سفارش</a></li>
                    <li><a href="/blog" class="hover:text-white transition">وبلاگ و ترفندهای اینستاگرام</a></li>
                    <li><a href="/admin" class="hover:text-white transition">ورود همکاران (پنل ادمین)</a></li>
                </ul>
            </div>
            <div>
                <h5 class="text-white font-bold text-sm mb-3">پشتیبانی و ارتباط</h5>
                <p class="mb-2">پشتیبانی تلگرام: <a href="https://t.me/sepehrmamouri" class="text-white font-mono dir-ltr">@sepehrmamouri</a></p>
                <p class="mb-4">پاسخگویی آنلاین در ۷ روز هفته</p>
                <div class="flex gap-2">
                    <span class="p-2 rounded-lg bg-slate-800 text-white"><i class="fa-solid fa-credit-card"></i> پرداخت شتابی</span>
                    <span class="p-2 rounded-lg bg-slate-800 text-white"><i class="fa-solid fa-shield"></i> امنیت SSL</span>
                </div>
            </div>
        </div>
        <div class="border-t border-slate-800 pt-6 text-center text-slate-500 text-[11px]">
            © ۲۰۲۶ تمامی حقوق محفوظ است - پلتفرم هوشمند سپهر فالوور.
        </div>
    </footer>

    <!-- Bottom Navigation اختصاصی موبایل (مشابه اپلیکیشن دیجی‌کالا) -->
    <div class="fixed bottom-0 inset-x-0 bg-white border-t flex justify-around py-2 px-1 z-40 md:hidden text-[10px] text-slate-600 font-semibold shadow-lg">
        <a href="/" class="flex flex-col items-center gap-1 hover:text-brand-dk active:text-brand-dk">
            <i class="fa-solid fa-house text-lg"></i>
            <span>خانه</span>
        </a>
        <a href="#services" class="flex flex-col items-center gap-1 hover:text-brand-dk">
            <i class="fa-solid fa-cubes text-lg"></i>
            <span>خدمات</span>
        </a>
        <a href="/track" class="flex flex-col items-center gap-1 hover:text-brand-dk text-brand-dk font-bold">
            <i class="fa-solid fa-truck-ramp-box text-lg"></i>
            <span>پیگیری</span>
        </a>
        <a href="/blog" class="flex flex-col items-center gap-1 hover:text-brand-dk">
            <i class="fa-solid fa-newspaper text-lg"></i>
            <span>آموزش</span>
        </a>
    </div>

    <!-- مودال ثبت سفارش خرید سریع -->
    <div id="orderModal" class="hidden fixed inset-0 bg-black/60 modal-blur z-50 flex items-center justify-center p-4">
        <div class="bg-white w-full max-w-md rounded-3xl p-6 shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <button onclick="closeModal()" class="absolute left-5 top-5 text-slate-400 hover:text-slate-600 text-xl font-bold">✕</button>
            
            <div class="flex items-center gap-3 mb-4">
                <span class="w-10 h-10 rounded-xl bg-red-100 text-brand-dk flex items-center justify-center text-lg">
                    <i class="fa-solid fa-bag-shopping"></i>
                </span>
                <div>
                    <h3 class="text-base font-black text-slate-900">تکمیل سفارش و پرداخت</h3>
                    <p class="text-xs text-slate-400">بدون نیاز به رمز عبور پیج شما</p>
                </div>
            </div>

            <div class="bg-slate-50 p-4 rounded-2xl mb-5 border border-slate-100">
                <div class="flex justify-between items-center text-xs mb-1 font-bold text-slate-700">
                    <span>پکیج انتخابی:</span>
                    <span id="modalPkgTitle" class="text-slate-900 font-black">---</span>
                </div>
                <div class="flex justify-between items-center text-xs text-slate-500">
                    <span>مبلغ قابل پرداخت:</span>
                    <span id="modalPkgPrice" class="text-brand-dk font-black text-sm">---</span>
                </div>
            </div>

            <form action="/checkout" method="POST" class="space-y-4">
                <input type="hidden" name="package_id" id="modalPkgId">
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">
                        <i class="fa-brands fa-instagram text-rose-600 ml-1"></i> آیدی اینستاگرام پیج یا لینک پست:
                    </label>
                    <input type="text" name="target" placeholder="مثال: sepehr_page یا لینک ریلز" dir="ltr" required
                           class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-dk focus:bg-white transition">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">
                        <i class="fa-solid fa-mobile-screen text-slate-600 ml-1"></i> شماره تماس جهت دریافت کد پیگیری پیامکی:
                    </label>
                    <input type="tel" name="phone" placeholder="۰۹۱۲۳۴۵۶۷۸۹" dir="ltr" required
                           class="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-brand-dk focus:bg-white transition">
                </div>
                
                <div class="bg-rose-50 text-brand-dk text-[11px] p-3 rounded-xl flex items-center gap-2">
                    <i class="fa-solid fa-circle-check text-base"></i>
                    <span>پیج شما در طول انجام سفارش حتماً باید در حالت <b>عمومی (Public)</b> باشد.</span>
                </div>

                <button type="submit" class="w-full bg-brand-dk hover:bg-red-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-red-200 transition flex items-center justify-center gap-2 text-sm">
                    <i class="fa-solid fa-lock"></i> پرداخت امن بانکی و شروع سفارش
                </button>
            </form>
        </div>
    </div>

    <script>
        function openOrderModal(id, title, price) {
            document.getElementById('modalPkgId').value = id;
            document.getElementById('modalPkgTitle').innerText = title;
            document.getElementById('modalPkgPrice').innerText = Number(price).toLocaleString('fa-IR') + ' تومان';
            document.getElementById('orderModal').classList.remove('hidden');
        }
        function closeModal() {
            document.getElementById('orderModal').classList.add('hidden');
        }
        function switchTab(categoryId) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            const btn = document.getElementById('btn-' + categoryId);
            const content = document.getElementById('tab-' + categoryId);
            if(btn) btn.classList.add('active');
            if(content) content.classList.add('active');
        }
    </script>
</body>
</html>
"""

# --- صفحه اصلی (ترکیب ایران فالوور و دیجی‌کالا) ---
INDEX_CONTENT = """
{% extends "base" %}
{% block content %}
<!-- بخش هیرو و آمار ایران فالوور -->
<section class="max-w-7xl mx-auto px-4 pt-10 pb-8">
    <div class="bg-gradient-to-br from-slate-900 via-slate-800 to-rose-950 text-white rounded-3xl p-8 md:p-12 relative overflow-hidden shadow-2xl">
        <div class="relative z-10 max-w-3xl">
            <span class="inline-flex items-center gap-2 bg-rose-600/30 border border-rose-500/40 text-rose-300 text-xs font-bold px-3 py-1 rounded-full mb-4">
                <i class="fa-solid fa-rocket"></i> افزایش تصاعدی فروش در اینستاگرام
            </span>
            <h1 class="text-3xl md:text-5xl font-black leading-tight mb-4">
                خرید فالوور، لایک و ویو اینستاگرام <br>
                <span class="text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-pink-400 to-rose-400">تحویل آنی + گارانتی ۳۰ روزه ریزش</span>
            </h1>
            <p class="text-slate-300 text-sm md:text-base leading-relaxed mb-8 max-w-2xl">
                با معتبرترین پلتفرم ارائه‌دهنده خدمات سوشال مدیا، اعتبار پیج خود را چند برابر کنید و با سیگنال‌های مثبت به اکسپلور راه پیدا کنید.
            </p>
            <div class="flex flex-wrap gap-4">
                <a href="#services" class="bg-brand-dk hover:bg-red-700 text-white font-bold text-sm px-6 py-3.5 rounded-xl shadow-lg shadow-rose-900/50 transition flex items-center gap-2">
                    <i class="fa-solid fa-cart-arrow-down"></i> مشاهده لیست تعرفه‌ها
                </a>
                <a href="/track" class="bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-sm px-6 py-3.5 rounded-xl transition flex items-center gap-2">
                    <i class="fa-solid fa-magnifying-glass"></i> پیگیری سفارش ثبت شده
                </a>
            </div>
        </div>

        <!-- آمارهای اعتمادساز -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-10 pt-8 border-t border-white/10 text-center">
            <div>
                <div class="text-2xl md:text-3xl font-black text-rose-400">۵+ سال</div>
                <div class="text-[11px] text-slate-400 font-semibold mt-1">سابقه خدمات حرفه‌ای</div>
            </div>
            <div>
                <div class="text-2xl md:text-3xl font-black text-rose-400">+۸۵۰,۰۰۰</div>
                <div class="text-[11px] text-slate-400 font-semibold mt-1">سفارش موفق و تحویل شده</div>
            </div>
            <div>
                <div class="text-2xl md:text-3xl font-black text-rose-400">۱۰۰٪ آنی</div>
                <div class="text-[11px] text-slate-400 font-semibold mt-1">پردازش خودکار سرور</div>
            </div>
            <div>
                <div class="text-2xl md:text-3xl font-black text-rose-400">بدون پسورد</div>
                <div class="text-[11px] text-slate-400 font-semibold mt-1">امنیت کامل پیج شما</div>
            </div>
        </div>
    </div>
</section>

<!-- بخش شگفت‌انگیزها (Incredible Offers) دیجی‌کالایی -->
<section id="incredible" class="max-w-7xl mx-auto px-4 py-8">
    <div class="bg-brand-dk rounded-3xl p-6 text-white shadow-xl shadow-red-200">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4 mb-6">
            <div class="flex items-center gap-3">
                <span class="text-3xl font-black"><i class="fa-solid fa-bolt-lightning text-yellow-300"></i> پیشنهادهای شگفت‌انگیز</span>
                <span class="bg-white text-brand-dk text-xs font-black px-3 py-1 rounded-full">تخفیف محدود</span>
            </div>
            <p class="text-xs text-rose-100">پرفروش‌ترین پکیج‌های ارتقای تضمینی اینستاگرام با بالاترین تخفیف</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            {% for pkg in special_packages %}
            <div class="bg-white text-slate-800 rounded-2xl p-5 dk-shadow flex flex-col justify-between hover:scale-[1.02] transition duration-200">
                <div>
                    <div class="flex justify-between items-center mb-3">
                        <span class="bg-rose-100 text-brand-dk text-xs font-black px-2.5 py-1 rounded-lg">{{ pkg.badge or 'شگفت‌انگیز' }}</span>
                        {% if pkg.old_price %}
                        <span class="text-xs bg-red-600 text-white font-bold px-2 py-0.5 rounded-full">
                            {{ (((pkg.old_price - pkg.price) / pkg.old_price) * 100) | round | int }}% تخفیف
                        </span>
                        {% endif %}
                    </div>
                    <h3 class="font-black text-base text-slate-900 mb-2">{{ pkg.title }}</h3>
                    <ul class="text-xs text-slate-600 space-y-2 mb-6">
                        {% for f in pkg.features.split('|') %}
                        <li class="flex items-center gap-2"><i class="fa-solid fa-check text-emerald-500 text-[10px]"></i> {{ f }}</li>
                        {% endfor %}
                    </ul>
                </div>
                <div>
                    <div class="flex justify-between items-end border-t pt-4 mb-4">
                        <div class="text-xs text-slate-400 line-through">{{ "{:,}".format(pkg.old_price) if pkg.old_price else '' }}</div>
                        <div class="text-xl font-black text-brand-dk">{{ "{:,}".format(pkg.price) }} <span class="text-xs font-normal text-slate-500">تومان</span></div>
                    </div>
                    <button onclick="openOrderModal({{ pkg.id }}, '{{ pkg.title }}', {{ pkg.price }})" 
                            class="w-full bg-brand-dk hover:bg-red-700 text-white font-bold py-3 rounded-xl text-xs shadow-md transition flex items-center justify-center gap-2">
                        <i class="fa-solid fa-cart-shopping"></i> سفارش سریع شگفت‌انگیز
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</section>

<!-- بخش دسته‌بندی تب‌دار ایران فالوور -->
<section id="services" class="max-w-7xl mx-auto px-4 py-8">
    <div class="text-center mb-8">
        <h2 class="text-2xl md:text-3xl font-black text-slate-900 mb-2">تعرفه‌ها و خدمات هوشمند اینستاگرام</h2>
        <p class="text-slate-500 text-xs md:text-sm">سرویس مورد نظر خود را انتخاب کنید و در کمتر از ۲ دقیقه سفارش دهید</p>
    </div>

    <!-- دکمه‌های سوئیچ تب دسته‌بندی -->
    <div class="flex flex-wrap justify-center gap-2 mb-8">
        <button id="btn-follower_ir" onclick="switchTab('follower_ir')" class="tab-btn active px-5 py-2.5 rounded-2xl text-xs md:text-sm font-bold border border-slate-200 bg-white transition flex items-center gap-2">
            <i class="fa-solid fa-users text-rose-500"></i> فالوور ایرانی واقعی
        </button>
        <button id="btn-follower_cheap" onclick="switchTab('follower_cheap')" class="tab-btn px-5 py-2.5 rounded-2xl text-xs md:text-sm font-bold border border-slate-200 bg-white transition flex items-center gap-2">
            <i class="fa-solid fa-bolt text-amber-500"></i> فالوور ارزان و فوری
        </button>
        <button id="btn-like" onclick="switchTab('like')" class="tab-btn px-5 py-2.5 rounded-2xl text-xs md:text-sm font-bold border border-slate-200 bg-white transition flex items-center gap-2">
            <i class="fa-solid fa-heart text-red-500"></i> لایک اکسپلور
        </button>
        <button id="btn-view" onclick="switchTab('view')" class="tab-btn px-5 py-2.5 rounded-2xl text-xs md:text-sm font-bold border border-slate-200 bg-white transition flex items-center gap-2">
            <i class="fa-solid fa-play text-blue-500"></i> ویو ویدیو و ریلز
        </button>
        <button id="btn-comment" onclick="switchTab('comment')" class="tab-btn px-5 py-2.5 rounded-2xl text-xs md:text-sm font-bold border border-slate-200 bg-white transition flex items-center gap-2">
            <i class="fa-solid fa-comment-dots text-emerald-500"></i> کامنت دلخواه
        </button>
    </div>

    <!-- محتوای دسته‌ها -->
    {% for cat_id, cat_packages in categorized_packages.items() %}
    <div id="tab-{{ cat_id }}" class="tab-content {% if loop.first %}active{% endif %}">
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {% for pkg in cat_packages %}
            <div class="bg-white rounded-3xl p-6 border border-slate-100 dk-shadow dk-shadow-hover transition duration-200 flex flex-col justify-between">
                <div>
                    {% if pkg.badge %}
                    <span class="inline-block bg-slate-100 text-slate-700 text-[10px] font-black px-3 py-1 rounded-full mb-3">{{ pkg.badge }}</span>
                    {% endif %}
                    <h3 class="font-black text-base text-slate-900 mb-2">{{ pkg.title }}</h3>
                    <div class="text-xs text-slate-400 mb-4 line-through">{{ "{:,}".format(pkg.old_price) if pkg.old_price else '' }}</div>
                    
                    <div class="text-2xl font-black text-slate-900 mb-6">
                        {{ "{:,}".format(pkg.price) }} <span class="text-xs font-normal text-slate-400">تومان</span>
                    </div>

                    <ul class="text-xs text-slate-600 space-y-2.5 mb-6 border-t pt-4">
                        {% for f in pkg.features.split('|') %}
                        <li class="flex items-center gap-2">
                            <i class="fa-solid fa-check text-brand-dk text-xs"></i> {{ f }}
                        </li>
                        {% endfor %}
                    </ul>
                </div>

                <button onclick="openOrderModal({{ pkg.id }}, '{{ pkg.title }}', {{ pkg.price }})" 
                        class="w-full bg-slate-900 hover:bg-brand-dk text-white font-bold py-3 rounded-2xl text-xs transition duration-200 flex items-center justify-center gap-2 shadow-sm">
                    <i class="fa-solid fa-cart-shopping"></i> ثبت و پرداخت آنلاین
                </button>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
</section>

<!-- بخش سوالات متداول (FAQ) -->
<section class="max-w-4xl mx-auto px-4 py-12">
    <div class="text-center mb-8">
        <h3 class="text-xl font-black text-slate-900 mb-2">سوالات متداول کاربران</h3>
        <p class="text-xs text-slate-500">پاسخ به سوالاتی که ممکن است قبل از خرید برای شما پیش بیاید</p>
    </div>
    <div class="space-y-4">
        <div class="bg-white p-5 rounded-2xl border border-slate-100 dk-shadow">
            <h4 class="font-bold text-sm text-slate-900 mb-2 flex items-center gap-2">
                <i class="fa-solid fa-circle-question text-brand-dk"></i> آیا برای سفارش نیاز به رمز عبور اینستاگرام است؟
            </h4>
            <p class="text-xs text-slate-600 leading-relaxed">
                خیر، به هیچ وجه! برای انجام هیچ یک از خدمات سپهر فالوور نیازی به کلمه عبور پیج شما نیست. تنها داشتن آیدی عمومی (Public) پیج کافی است.
            </p>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-100 dk-shadow">
            <h4 class="font-bold text-sm text-slate-900 mb-2 flex items-center gap-2">
                <i class="fa-solid fa-circle-question text-brand-dk"></i> چقدر طول می‌کشد تا سفارش من انجام شود؟
            </h4>
            <p class="text-xs text-slate-600 leading-relaxed">
                اکثر سفارش‌ها بین ۲ تا ۱۵ دقیقه پس از پرداخت موفق به صورت آنی استارت می‌خورند و بستگی به حجم پکیج با سرعت طبیعی تکمیل می‌گردند.
            </p>
        </div>
        <div class="bg-white p-5 rounded-2xl border border-slate-100 dk-shadow">
            <h4 class="font-bold text-sm text-slate-900 mb-2 flex items-center gap-2">
                <i class="fa-solid fa-circle-question text-brand-dk"></i> چطور سفارشم را پیگیری کنم؟
            </h4>
            <p class="text-xs text-slate-600 leading-relaxed">
                بلافاصله پس از ثبت سفارش یک کد اختصاصی (مانند SF-123456) دریافت می‌کنید که می‌توانید با وارد کردن آن در بخش «پیگیری سفارش»، وضعیت لحظه‌ای ارسال را مشاهده کنید.
            </p>
        </div>
    </div>
</section>
{% endblock %}
"""

# --- صفحه پیگیری سفارش مرحله‌ای دیجی‌کالایی (/track) ---
TRACK_PAGE = """
{% extends "base" %}
{% block content %}
<div class="max-w-2xl mx-auto px-4 py-12">
    <div class="bg-white rounded-3xl p-8 border border-slate-100 shadow-xl">
        <div class="text-center mb-8">
            <div class="w-16 h-16 rounded-3xl bg-red-50 text-brand-dk flex items-center justify-center text-2xl mx-auto mb-3">
                <i class="fa-solid fa-truck-fast"></i>
            </div>
            <h1 class="text-2xl font-black text-slate-900">سامانه هوشمند پیگیری سفارش</h1>
            <p class="text-xs text-slate-500 mt-1">کد رهگیری دریافتی (مثال: SF-XXXXXX) را وارد کنید</p>
        </div>

        <form method="GET" action="/track" class="flex gap-2 mb-8">
            <input type="text" name="code" value="{{ search_code or '' }}" placeholder="کد رهگیری SF-..." dir="ltr" required
                   class="flex-grow bg-slate-50 border border-slate-200 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:border-brand-dk uppercase font-mono font-bold">
            <button type="submit" class="bg-brand-dk hover:bg-red-700 text-white font-bold px-6 py-3 rounded-2xl text-xs transition flex items-center gap-2 shadow-md">
                <i class="fa-solid fa-magnifying-glass"></i> استعلام
            </button>
        </form>

        {% if order %}
        <div class="border-t pt-6">
            <div class="flex justify-between items-center mb-6">
                <div>
                    <span class="text-xs text-slate-400">شناسه پیگیری:</span>
                    <div class="text-base font-black font-mono text-slate-900">{{ order.tracking_code }}</div>
                </div>
                <div>
                    {% if order.status == 'completed' %}
                        <span class="bg-emerald-100 text-emerald-700 text-xs font-black px-3 py-1.5 rounded-full"><i class="fa-solid fa-check"></i> تکمیل شده</span>
                    {% elif order.status == 'processing' %}
                        <span class="bg-blue-100 text-blue-700 text-xs font-black px-3 py-1.5 rounded-full"><i class="fa-solid fa-spinner fa-spin"></i> در حال ارسال</span>
                    {% else %}
                        <span class="bg-amber-100 text-amber-700 text-xs font-black px-3 py-1.5 rounded-full"><i class="fa-solid fa-clock"></i> در صف بررسی</span>
                    {% endif %}
                </div>
            </div>

            <!-- وضعیت مرحله‌ای مشابه دیجی‌کالا -->
            <div class="relative flex justify-between items-center mb-8 px-4">
                <div class="text-center z-10">
                    <div class="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs mx-auto mb-1">✓</div>
                    <span class="text-[10px] font-bold text-slate-700">ثبت سفارش</span>
                </div>
                <div class="text-center z-10">
                    <div class="w-8 h-8 rounded-full {% if order.status in ['processing', 'completed'] %}bg-emerald-500 text-white{% else %}bg-slate-200 text-slate-500{% endif %} flex items-center justify-center text-xs mx-auto mb-1">
                        {% if order.status in ['processing', 'completed'] %}✓{% else %}۲{% endif %}
                    </div>
                    <span class="text-[10px] font-bold text-slate-700">تایید درگاه</span>
                </div>
                <div class="text-center z-10">
                    <div class="w-8 h-8 rounded-full {% if order.status in ['processing', 'completed'] %}bg-brand-dk text-white animate-pulse{% else %}bg-slate-200 text-slate-500{% endif %} flex items-center justify-center text-xs mx-auto mb-1">
                        <i class="fa-solid fa-paper-plane text-[10px]"></i>
                    </div>
                    <span class="text-[10px] font-bold text-slate-700">ارسال به پیج</span>
                </div>
                <div class="text-center z-10">
                    <div class="w-8 h-8 rounded-full {% if order.status == 'completed' %}bg-emerald-500 text-white{% else %}bg-slate-200 text-slate-500{% endif %} flex items-center justify-center text-xs mx-auto mb-1">
                        {% if order.status == 'completed' %}✓{% else %}۴{% endif %}
                    </div>
                    <span class="text-[10px] font-bold text-slate-700">تکمیل نهایی</span>
                </div>
            </div>

            <div class="bg-slate-50 rounded-2xl p-4 space-y-2 text-xs">
                <div class="flex justify-between"><span class="text-slate-500">پکیج:</span><span class="font-bold text-slate-800">{{ order.package_title }}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">آیدی مقصد:</span><span class="font-mono font-bold text-slate-800">{{ order.target_input }}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">مبلغ پرداخت شده:</span><span class="font-bold text-emerald-600">{{ "{:,}".format(order.amount) }} تومان</span></div>
                <div class="flex justify-between"><span class="text-slate-500">تاریخ ثبت:</span><span class="font-mono text-slate-600">{{ order.created_at }}</span></div>
            </div>
        </div>
        {% elif search_code %}
        <div class="bg-rose-50 text-brand-dk p-4 rounded-2xl text-xs text-center font-bold">
            سفارشی با کد پیگیری وارد شده یافت نشد. لطفاً کد را مجدداً بررسی کنید.
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
"""

# --- روت‌ها و کنترلرهای بک‌اِند ---

@app.route("/")
def index():
    with get_db() as conn:
        all_pkgs = conn.execute("SELECT * FROM packages").fetchall()
        special_pkgs = conn.execute("SELECT * FROM packages WHERE is_special = 1 LIMIT 3").fetchall()
        
        # دسته‌بندی برای تب‌ها
        categorized = {}
        for p in all_pkgs:
            cat = p['category']
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

    template = BASE_LAYOUT.replace("{% block content %}{% endblock %}", INDEX_CONTENT.replace('{% extends "base" %}{% block content %}', '').replace('{% endblock %}', ''))
    return render_template_string(template, special_packages=special_pkgs, categorized_packages=categorized)

@app.route("/checkout", methods=["POST"])
def checkout():
    pkg_id = request.form.get("package_id")
    target = request.form.get("target", "").strip()
    phone = request.form.get("phone", "").strip()

    if not pkg_id or not target or not phone:
        return "اطلاعات ارسالی ناقص است.", 400

    with get_db() as conn:
        pkg = conn.execute("SELECT * FROM packages WHERE id = ?", (pkg_id,)).fetchone()
        if not pkg:
            return "پکیج معتبر نیست.", 404

        tracking_code = generate_tracking_code()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (tracking_code, package_id, package_title, category, target_input, phone, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'processing')
        ''', (tracking_code, pkg['id'], pkg['title'], pkg['category'], target, phone, pkg['price']))
        conn.commit()

    # در محیط لایو، هدایت به درگاه پرداخت انجام می‌شود؛ برای شروع مستقیم به رهگیری منتقل می‌شود
    return redirect(url_for('track_order', code=tracking_code))

@app.route("/track")
def track_order():
    code = request.args.get("code", "").strip().upper()
    order = None
    if code:
        with get_db() as conn:
            order = conn.execute("SELECT * FROM orders WHERE tracking_code = ?", (code,)).fetchone()

    template = BASE_LAYOUT.replace("{% block content %}{% endblock %}", TRACK_PAGE.replace('{% extends "base" %}{% block content %}', '').replace('{% endblock %}', ''))
    return render_template_string(template, order=order, search_code=code, title="پیگیری سفارش | سپهر فالوور")

@app.route("/blog")
def blog_list():
    with get_db() as conn:
        posts = conn.execute("SELECT * FROM blog_posts ORDER BY id DESC").fetchall()
    
    blog_html = """
    <div class="max-w-4xl mx-auto px-4 py-12">
        <h1 class="text-2xl font-black text-slate-900 mb-8 text-center">وبلاگ و آموزش‌های رشد اینستاگرام</h1>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {% for post in posts %}
            <div class="bg-white rounded-3xl p-6 border border-slate-100 dk-shadow">
                <h2 class="font-black text-base text-slate-900 mb-2">{{ post.title }}</h2>
                <p class="text-xs text-slate-500 leading-relaxed mb-4">{{ post.excerpt }}</p>
                <div class="text-[11px] text-slate-400 font-mono">{{ post.created_at }}</div>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    template = BASE_LAYOUT.replace("{% block content %}{% endblock %}", blog_html)
    return render_template_string(template, posts=posts, title="وبلاگ سپهر فالوور")

# --- پنل مدیریت ادمین ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        user = request.form.get("username")
        pw = request.form.get("password")
        if user == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, pw):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        error = "نام کاربری یا رمز عبور اشتباه است."
    
    login_html = """
    <div class="min-h-screen flex items-center justify-center bg-slate-100 p-4">
        <div class="bg-white max-w-sm w-full p-8 rounded-3xl shadow-xl border">
            <h2 class="text-xl font-black text-center mb-6">ورود به پنل مدیریت</h2>
            {% if error %}<div class="bg-red-50 text-red-600 text-xs p-3 rounded-xl mb-4 text-center">{{ error }}</div>{% endif %}
            <form method="POST" class="space-y-4">
                <input type="text" name="username" placeholder="نام کاربری" required class="w-full bg-slate-50 border p-3 rounded-xl text-xs">
                <input type="password" name="password" placeholder="رمز عبور" required class="w-full bg-slate-50 border p-3 rounded-xl text-xs">
                <button type="submit" class="w-full bg-rose-600 text-white font-bold py-3 rounded-xl text-xs">ورود</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(login_html, error=error)

@app.route("/admin")
@login_required
def admin_dashboard():
    with get_db() as conn:
        orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        total_orders = len(orders)
        total_revenue = sum(o['amount'] for o in orders)
    
    admin_html = """
    <div class="max-w-7xl mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-2xl font-black">داشبورد مدیریت سپهر فالوور</h1>
            <a href="/admin/logout" class="text-xs bg-red-100 text-red-600 px-4 py-2 rounded-xl font-bold">خروج</a>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mb-8">
            <div class="bg-white p-6 rounded-2xl border shadow-sm"><div class="text-slate-400 text-xs">کل سفارش‌ها</div><div class="text-2xl font-black">{{ total_orders }}</div></div>
            <div class="bg-white p-6 rounded-2xl border shadow-sm"><div class="text-slate-400 text-xs">مجموع فروش</div><div class="text-2xl font-black text-emerald-600">{{ "{:,}".format(total_revenue) }} تومان</div></div>
        </div>

        <div class="bg-white rounded-2xl border shadow-sm overflow-x-auto">
            <table class="w-full text-right text-xs">
                <thead class="bg-slate-50 border-b">
                    <tr>
                        <th class="p-4">کد پیگیری</th>
                        <th class="p-4">پکیج</th>
                        <th class="p-4">مقصد / پیج</th>
                        <th class="p-4">شماره تماس</th>
                        <th class="p-4">مبلغ</th>
                        <th class="p-4">وضعیت</th>
                    </tr>
                </thead>
                <tbody class="divide-y">
                    {% for o in orders %}
                    <tr>
                        <td class="p-4 font-mono font-bold">{{ o.tracking_code }}</td>
                        <td class="p-4">{{ o.package_title }}</td>
                        <td class="p-4 font-mono dir-ltr">{{ o.target_input }}</td>
                        <td class="p-4 font-mono">{{ o.phone }}</td>
                        <td class="p-4 font-bold">{{ "{:,}".format(o.amount) }}</td>
                        <td class="p-4"><span class="px-2 py-1 rounded bg-slate-100">{{ o.status }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    """
    return render_template_string(admin_html, orders=orders, total_orders=total_orders, total_revenue=total_revenue)

@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# --- سئو: سایت‌مپ و روبات‌ها ---
@app.route("/sitemap.xml")
def sitemap():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>
        <url><loc>{SITE_URL}/track</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
        <url><loc>{SITE_URL}/blog</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
    </urlset>"""
    return Response(xml, mimetype="application/xml")

@app.route("/robots.txt")
def robots():
    txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml"
    return Response(txt, mimetype="text/plain")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

