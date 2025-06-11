# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'postgresql://postgres:password@localhost/kurasmart'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
