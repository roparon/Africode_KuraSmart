import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "default-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///kura.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Login / Session Settings
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # Remember me session duration

    # JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    # JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
