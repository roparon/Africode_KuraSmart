from datetime import datetime
from app.extensions import db
from sqlalchemy.sql import func
from flask_login import UserMixin



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='voter')
    id_number = db.Column(db.String(20), unique=True)
    username = db.Column(db.String(80), unique=True)
    county = db.Column(db.String(100))
    constituency = db.Column(db.String(100))
    ward = db.Column(db.String(100))
    sub_location = db.Column(db.String(100))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    deactivated_by = db.Column(db.Integer, db.ForeignKey('user.id'))


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    party_name = db.Column(db.String(100))
    position = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manifesto = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='candidates')
    election = db.relationship('Election', backref='candidates')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'election_id': self.election_id,
            'full_name': self.full_name,
            'party_name': self.party_name,
            'position': self.position,
            'description': self.description,
            'manifesto': self.manifesto,
            'approved': self.approved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    voter = db.relationship('User', backref='votes')
    election = db.relationship('Election', backref='votes')
    candidate = db.relationship('Candidate', backref='votes')


class VerificationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref='verification_requests')
