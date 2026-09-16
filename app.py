from flask import Flask
from config import Config
from database import init_db

# ایمپورت کردن Blueprintها
from blueprints.main import main_bp
from blueprints.order import order_bp
from blueprints.admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# ساخت دیتابیس در اولین اجرا
with app.app_context():
    init_db()

# ثبت (Register) بلپرینت‌ها در برنامه
app.register_blueprint(main_bp)
app.register_blueprint(order_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True)

