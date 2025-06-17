import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or 'you-should-set-this-in-env'
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or 'sqlite:///dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    # Flask-Login session config (optional tweaks)
    SESSION_COOKIE_SECURE = False  
    REMEMBER_COOKIE_DURATION = 3600  
