from datetime import datetime
from app.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    id_number = db.Column(db.String(20), unique=True, nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    county = db.Column(db.String(50))
    constituency = db.Column(db.String(50))
    ward = db.Column(db.String(50))
    sub_location = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
