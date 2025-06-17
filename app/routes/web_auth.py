from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from app.forms.forms import LoginForm, RegistrationForm
from app.models import User, Election, Candidate, Vote, Position
from app.extensions import db
from datetime import datetime

web_auth_bp = Blueprint('web_auth', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
voter_bp = Blueprint('voter', __name__, url_prefix='/voter')


def super_admin_required(f):
    """
    Decorator to restrict access to super admins only.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You need to log in first.', 'warning')
            return redirect(url_for('web_auth.login'))
        if not current_user.is_superadmin:
            flash('Access denied: Super Admins only.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


# User Registration
@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email is already registered.', 'danger')
            return render_template('register.html', form=form)

        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            role='voter'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash(f'Welcome {user.full_name}! Registration successful. Please log in.', 'success')
        return redirect(url_for('web_auth.login'))

    return render_template('register.html', form=form)


# User Login
@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')

            # Redirect based on privileges
            if user.is_superadmin:
                return redirect(url_for('admin.dashboard'))
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voter.voter_dashboard'))

        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


# Super Admin / Admin Dashboard
@admin_bp.route('/dashboard')
@login_required
@super_admin_required
def dashboard():
    """Accessible only to super admins."""
    return render_template('admin/dashboard.html')


# Voter Dashboard
@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    if current_user.role != 'voter':
        abort(403)

    elections = Election.query.filter(Election.end_date >= datetime.utcnow()).all()
    votes = Vote.query.filter_by(voter_id=current_user.id).all()

    vote_records = []
    for vote in votes:
        vote_records.append({
            "candidate_name": Candidate.query.get(vote.candidate_id).full_name,
            "position_name": Position.query.get(vote.position_id).name,
            "election_title": Election.query.get(vote.election_id).title,
            "voted_at": vote.created_at.strftime("%Y-%m-%d %H:%M")
        })

    return render_template('voter/dashboard.html', elections=elections, votes=vote_records)


# Logout
@web_auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.full_name
    logout_user()
    flash(f'{name}, you have logged out successfully.', 'info')
    return redirect(url_for('web_auth.login'))
