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

    TIMEZONE = 'Africa/Nairobi'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('qwis vidv yngm qbxi')
    MAIL_DEFAULT_SENDER = MAIL_USERNAME

 
