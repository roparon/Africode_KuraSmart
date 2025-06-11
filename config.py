import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///kura.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configurations ##
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # short-lived access token
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)    # long-lived refresh token
