from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.enums import ElectionStatusEnum
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum
import enum
from enum import Enum

class UserRole(enum.Enum):
    voter = "voter"
    candidate = "candidate"
    admin = "admin"
    super_admin = "super_admin"
role = db.Column(SQLAlchemyEnum(UserRole, name='userrole'), nullable=False)


class ElectionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True)
    id_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    voting_type = db.Column(db.String(10), nullable=False, default="informal")
    national_id = db.Column(db.String(20), unique=True, nullable=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    county = db.Column(db.String(100), nullable=True)
    sub_county = db.Column(db.String(100), nullable=True)
    division = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    sub_location = db.Column(db.String(100), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True, default='profile_images/default-profile.png')
    is_verified = db.Column(db.Boolean, default=False, index=True)
    is_superadmin = db.Column(db.Boolean, default=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.voter, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    candidates = db.relationship('Candidate', back_populates='user', lazy='dynamic')
    verification_requests = db.relationship('VerificationRequest', back_populates='user', lazy='dynamic')
    votes = db.relationship('Vote', back_populates='voter', lazy='dynamic')

    # Password logic
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Role checks
    def is_admin(self):
        return self.role in [UserRole.admin, UserRole.super_admin]

    def is_super_admin(self):
        return self.role == UserRole.super_admin

    def is_voter(self):
        return self.role == UserRole.voter

    def is_candidate(self):
        return self.role == UserRole.candidate

    # Token helpers
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        try:
            s = Serializer(current_app.config['SECRET_KEY'])
            data = s.loads(token, max_age=expires_sec)
            return User.query.get(data.get('user_id'))
        except Exception:
            return None

    def __repr__(self):
        return f"<User id={self.id}, email='{self.email}', role='{self.role.value}', voting_type='{self.voting_type}'>"

    def __str__(self):
        return self.full_name


from zoneinfo import ZoneInfo
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
    candidates = db.relationship('Candidate', back_populates='election', lazy='select')
    positions = db.relationship('Position', back_populates='election', lazy='select', cascade="all, delete-orphan")
    votes = db.relationship('Vote', back_populates='election', lazy='select')

    def __repr__(self):
        return f"<Election id={self.id}, title='{self.title}', active={self.is_active}>"

    def __str__(self):
        return self.title
    
    @property
    def current_status(self):
        """Dynamically calculates election status based on dates and activity."""
        now = datetime.now(ZoneInfo("UTC"))  # Make 'now' timezone-aware

        start = self.start_date.replace(tzinfo=ZoneInfo("UTC"))
        end = self.end_date.replace(tzinfo=ZoneInfo("UTC"))

        if not self.is_active:
            return 'inactive'
        if now < start:
            return 'pending'
        elif start <= now <= end:
            return 'active'
        else:
            return 'ended'
class Candidate(db.Model):
    __tablename__ = 'candidate'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)

    full_name = db.Column(db.String(100), nullable=False)
    profile_photo = db.Column(db.String(255)) 
    party_name = db.Column(db.String(100))
    position = db.Column(db.String(100), nullable=True)
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
        return f"<Candidate id={self.id}, full_name='{self.full_name}', position='{self.position}', approved={self.approved}>"

    def __str__(self):
        return self.full_name

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)


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

    def __str__(self):
        return self.name

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

    def __str__(self):
        return f"Vote by User {self.voter_id} for Candidate {self.candidate_id} in Election {self.election_id}"

class VerificationRequest(db.Model):
    __tablename__ = 'verification_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    user = db.relationship('User', back_populates='verification_requests')

    def __repr__(self):
        return (f"<VerificationRequest id={self.id}, user_id={self.user_id}, status='{self.status}'>")

    def __str__(self):
        return f"VerificationRequest by User {self.user_id} ({self.status}) on {self.submitted_at.isoformat() if self.submitted_at else 'unknown date'}"
    

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    send_email = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_notifications_user_id_users'),
        nullable=False
    )
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.subject}>'




class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

    user = db.relationship('User', backref='audit_logs')