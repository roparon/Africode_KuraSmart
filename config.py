import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ------------------------
    # Security & Database
    # ------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "you-should-set-this-in-env")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///kura.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------
    # Sessionimport os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ------------------------
    # Security & Database
    # ------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "you-should-set-this-in-env")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///kura.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLAlchemy Engine Settings (important for production DBs like PostgreSQL)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800
    }

    # ------------------------
    # Session & Flask-Login
    # ------------------------
    SESSION_COOKIE_SECURE = False  # Set to True in production (HTTPS required)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False  # Set to True in production
    REMEMBER_COOKIE_NAME = 'remember_token'
    SESSION_PROTECTION = 'strong'

    # ------------------------
    # Flask-Mail
    # ------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "KuraSmart")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "KuraSmart <no-reply@kurasmart.com>")

    # ------------------------
    # App-wide Settings
    # ------------------------
    TIMEZONE = 'Africa/Nairobi'
    # ------------------------
    SESSION_COOKIE_SECURE = False  # Set True in production (HTTPS)
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False  # Set True in production
    REMEMBER_COOKIE_NAME = 'remember_token'
    SESSION_PROTECTION = 'strong'

    # ------------------------
    # Flask-Mail
    # ------------------------
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "KuraSmart")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "KuraSmart <no-reply@kurasmart.com>")

    # ------------------------
    # App-wide Settings
    # ------------------------
    TIMEZONE = 'Africa/Nairobi'
