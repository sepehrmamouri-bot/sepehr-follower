from flask import Blueprint, render_template, request
from database import get_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    with get_db() as conn:
        packages = conn.execute("SELECT * FROM packages").fetchall()
        blog_posts = conn.execute("SELECT * FROM blog ORDER BY id DESC LIMIT 3").fetchall()
    return render_template('index.html', packages=packages, blog_posts=blog_posts)

@main_bp.route('/services')
def services():
    with get_db() as conn:
        all_services = conn.execute("SELECT * FROM services WHERE is_active = 1 ORDER BY sort_order ASC").fetchall()
    return render_template('services.html', services=all_services)

@main_bp.route('/track')
@main_bp.route('/track/<code_arg>')
def track_order(code_arg=None):
    code = request.args.get('code') or code_arg
    order = None
    if code:
        with get_db() as conn:
            order = conn.execute("SELECT * FROM orders WHERE tracking_code = ?", (code.strip().upper(),)).fetchone()
    return render_template('track.html', order=order, search_code=code)

@main_bp.route('/blog')
def blog_list():
    with get_db() as conn:
        posts = conn.execute("SELECT * FROM blog ORDER BY id DESC").fetchall()
    return render_template('blog.html', posts=posts)

@main_bp.route('/blog/<slug>')
def blog_detail(slug):
    with get_db() as conn:
        post = conn.execute("SELECT * FROM blog WHERE slug = ?", (slug,)).fetchone()
    if not post:
        return "مقاله یافت نشد", 404
    return render_template('blog_detail.html', post=post)

@main_bp.route('/terms')
def terms():
    return render_template('base.html', page_content="<h3>قوانین و مقررات سپهر فالوور</h3><p style='margin-top:15px;'>۱. پیج اینستاگرام شما در حین انجام سفارش نباید Private (شخصی) باشد.<br>۲. مسئولیت وارد کردن آدرس صحیح با خریدار است.</p>")

@main_bp.route('/faq')
def faq():
    return render_template('base.html', page_content="<h3>سوالات متداول</h3><p style='margin-top:15px;'><b>آیا نیاز به پسورد پیج هست؟</b> خیر، هیچ رمزی دریافت نمی‌شود.<br><b>زمان شروع سفارش چقدر است؟</b> معمولاً کمتر از ۱۵ دقیقه.</p>")

@main_bp.route('/contact')
def contact():
    return render_template('base.html', page_content="<h3>تماس با ما</h3><p style='margin-top:15px;'>پشتیبانی تلگرام: @SepehrFollowerSupport<br>پاسخگویی ۲۴ ساعته در ۷ روز هفته.</p>")

