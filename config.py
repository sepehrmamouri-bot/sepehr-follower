import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "sepehr_secret_fallback_key_2026_ninja")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "sepehr_follower.db")
    
    # ادمین
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD_HASH = os.environ.get(
        "ADMIN_PASSWORD_HASH",
        "scrypt:32768:8:1$7U6rTj1GZ8bY4k...$..."  # رمز اولیه sepehr2026
    )
    
    # تنظیمات پنل مادر SMM
    SMM_API_URL = os.environ.get("SMM_API_URL", "https://justanotherpanel.com/api/v2")
    SMM_API_KEY = os.environ.get("SMM_API_KEY", "")
    
    # درگاه پرداخت زرین‌پال
    ZARINPAL_MERCHANT = os.environ.get("ZARINPAL_MERCHANT", "zarinpal_sandbox_mock_merchant_id")
    ZARINPAL_SANDBOX = os.environ.get("ZARINPAL_SANDBOX", "True").lower() == "true"
    ZARINPAL_CALLBACK_URL = os.environ.get("ZARINPAL_CALLBACK", "https://sepehrfollower.pythonanywhere.com/order/verify")

