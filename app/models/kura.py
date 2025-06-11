from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Voter(db.Model):
    __tablename__ = 'voters'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(20), unique=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    county = db.Column(db.String(100), nullable=False)
    constituency = db.Column(db.String(100), nullable=False)
    ward = db.Column(db.String(100), nullable=False)
    sub_location = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # super_admin or county_admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Election(db.Model):
    __tablename__ = 'elections'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete="SET NULL"))

    positions = db.relationship('Position', backref='election', cascade="all, delete-orphan")



class Position(db.Model):
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id', ondelete="CASCADE"))

    candidates = db.relationship('Candidate', backref='position', cascade="all, delete-orphan")



class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    party_name = db.Column(db.String(100), nullable=True)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id', ondelete="CASCADE"))

    votes = db.relationship('Vote', backref='candidate', cascade="all, delete-orphan")



class Vote(db.Model):
    __tablename__ = 'votes'
    
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voters.id', ondelete="CASCADE"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id', ondelete="CASCADE"), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id', ondelete="CASCADE"), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id', ondelete="CASCADE"), nullable=False)
    voted_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('voter_id', 'position_id', name='uix_vote_once_per_position'),
    )
