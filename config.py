import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Security ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///kura.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Apply engine options only if using PostgreSQL/MySQL (not SQLite)
    if "sqlite" not in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 1800
        }

    # --- Session & Login ---
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_NAME = 'remember_token'
    SESSION_PROTECTION = 'strong'

    # --- Flask-Mail ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "KuraSmart <no-reply@kurasmart.com>")

    # --- App-wide Settings ---
    TIMEZONE = 'Africa/Nairobi'
    SCHEDULER_API_ENABLED = True