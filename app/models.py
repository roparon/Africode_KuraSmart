from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.enums import ElectionStatusEnum
from sqlalchemy.sql import func
import enum
from enum import Enum

class UserRole(enum.Enum):
    voter = "voter"
    candidate = "candidate"
    admin = "admin"
    super_admin = "super_admin"

class ElectionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.voter, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    id_number = db.Column(db.String(20), unique=True, nullable=True)
    county = db.Column(db.String(100), nullable=True)
    constituency = db.Column(db.String(100), nullable=True)
    ward = db.Column(db.String(100), nullable=True)
    sub_location = db.Column(db.String(100), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    candidates = db.relationship('Candidate', back_populates='user', lazy='dynamic')
    verification_requests = db.relationship('VerificationRequest', back_populates='user', lazy='dynamic')
    votes = db.relationship('Vote', back_populates='voter', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role in [UserRole.admin, UserRole.super_admin]

    def is_super_admin(self):
        return self.role == UserRole.super_admin

    def is_voter(self):
        return self.role == UserRole.voter

    def is_candidate(self):
        return self.role == UserRole.candidate

    def __repr__(self):
        return f"<User id={self.id}, email='{self.email}', role='{self.role.value}'>"

class Election(db.Model):
    __tablename__ = 'election'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum(ElectionStatusEnum), nullable=False, default=ElectionStatusEnum.INACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    deactivated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    candidates = db.relationship('Candidate', back_populates='election', lazy='dynamic')
    positions = db.relationship('Position', back_populates='election', lazy='dynamic', cascade="all, delete-orphan")
    votes = db.relationship('Vote', back_populates='election', lazy='dynamic')

    def __repr__(self):
        return f"<Election id={self.id}, title='{self.title}', active={self.is_active}>"

class Candidate(db.Model):
    __tablename__ = 'candidate'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    party_name = db.Column(db.String(100))
    position = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    manifesto = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='candidates')
    election = db.relationship('Election', back_populates='candidates')
    position_rel = db.relationship('Position', back_populates='candidates')
    votes = db.relationship('Vote', back_populates='candidate', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'election_id': self.election_id,
            'position_id': self.position_id,
            'full_name': self.full_name,
            'party_name': self.party_name,
            'position': self.position,
            'description': self.description,
            'manifesto': self.manifesto,
            'approved': self.approved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return (f"<Candidate id={self.id}, full_name='{self.full_name}', "
                f"position='{self.position}', approved={self.approved}>")

class Position(db.Model):
    __tablename__ = 'position'

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    election = db.relationship('Election', back_populates='positions')
    candidates = db.relationship('Candidate', back_populates='position_rel', lazy='dynamic', cascade="all, delete-orphan")
    votes = db.relationship('Vote', back_populates='position', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position id={self.id}, name='{self.name}', election_id={self.election_id}>"

class Vote(db.Model):
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    voter = db.relationship('User', back_populates='votes')
    election = db.relationship('Election', back_populates='votes')
    candidate = db.relationship('Candidate', back_populates='votes')
    position = db.relationship('Position', back_populates='votes')

    __table_args__ = (
        db.UniqueConstraint('voter_id', 'election_id', 'position_id', name='uix_voter_election_position'),
    )

    def __repr__(self):
        return (f"<Vote id={self.id}, voter_id={self.voter_id}, election_id={self.election_id}, "
                f"position_id={self.position_id}, candidate_id={self.candidate_id}>")

class VerificationRequest(db.Model):
    __tablename__ = 'verification_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    user = db.relationship('User', back_populates='verification_requests')

    def __repr__(self):
        return (f"<VerificationRequest id={self.id}, user_id={self.user_id}, status='{self.status}'>")