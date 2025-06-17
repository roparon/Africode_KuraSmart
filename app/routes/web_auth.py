from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.forms import LoginForm, RegistrationForm, ElectionForm
from app.models import User, Election, Candidate, Vote, Position
from app.extensions import db
from datetime import datetime

# Blueprints
web_auth_bp = Blueprint('web_auth', __name__)
admin_web_bp = Blueprint('admin_web', __name__, url_prefix='/admin')
voter_bp = Blueprint('voter', __name__, url_prefix='/voter')


# -------------------------
# User Registration
# -------------------------
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


# -------------------------
# User Login
# -------------------------
@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')

            # Role-based redirection
            if user.is_superadmin or user.role == 'admin':
                return redirect(url_for('admin_web.dashboard'))
            return redirect(url_for('voter.voter_dashboard'))

        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


# -------------------------
# Admin Dashboard
# -------------------------
@admin_web_bp.route('/dashboard', endpoint='dashboard')
@login_required
def dashboard():
    if not (current_user.is_superadmin or current_user.role == 'admin'):
        abort(403)
    return render_template('admin/dashboard.html')


# -------------------------
# Admin Manage Users
# -------------------------
@admin_web_bp.route('/manage-users', endpoint='manage_users')
@login_required
def manage_users():
    if not (current_user.is_superadmin or current_user.role == 'admin'):
        abort(403)

    users = User.query.all()  # Adjust filter as needed
    return render_template('admin/manage_users.html', users=users)


# -------------------------
# Voter Dashboard
# -------------------------
@voter_bp.route('/dashboard', endpoint='voter_dashboard')
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


# -------------------------
# Logout
# -------------------------
@web_auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.full_name
    logout_user()
    flash(f'{name}, you have logged out successfully.', 'info')
    return redirect(url_for('web_auth.login'))


# -------------------------
# Admin Manage Elections
# -------------------------
@admin_web_bp.route('/manage-elections', endpoint='manage_elections')
@login_required
def manage_elections():
    if not (current_user.is_superadmin or current_user.role == 'admin'):
        abort(403)

    elections = Election.query.order_by(Election.start_date.desc()).all()
    return render_template('admin/manage_elections.html', elections=elections)



# -------------------------
# Admin View Analytics
# -------------------------
@admin_web_bp.route('/analytics', endpoint='view_analytics')
@login_required
def view_analytics():
    if not (current_user.is_superadmin or current_user.role == 'admin'):
        abort(403)

    total_users = User.query.count()
    total_votes = Vote.query.count()
    total_elections = Election.query.count()

    return render_template('admin/analytics.html', 
                           total_users=total_users, 
                           total_votes=total_votes, 
                           total_elections=total_elections)



@admin_web_bp.route('/elections/create', methods=['GET', 'POST'], endpoint='create_election')
@login_required
def create_election():
    if not (current_user.is_superadmin or current_user.role == 'admin'):
        abort(403)

    form = ElectionForm()
    if form.validate_on_submit():
        election = Election(
            title=form.title.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(election)
        db.session.commit()
        flash('Election created successfully!', 'success')
        return redirect(url_for('admin_web.dashboard'))

    return render_template('admin/create_election.html', form=form)

