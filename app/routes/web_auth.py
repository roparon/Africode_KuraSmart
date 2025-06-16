from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.forms import LoginForm, RegistrationForm
from app.models import User, Election, Candidate, Vote, Position
from app.extensions import db
from datetime import datetime

web_auth_bp = Blueprint('web_auth', __name__)
admin_bp = Blueprint('admin', __name__)
voter_bp = Blueprint('voter', __name__)


#user registration
@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
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

        flash(f'{user.full_name}, registered successful! Please log in.', 'success')
        return redirect(url_for('web_auth.login'))

    return render_template('register.html', form=form)



#User loginoroute

@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'{user.full_name} logged in successfully.', 'success')

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('voter.dashboard'))

        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        abort(403)
    return render_template('admin/dashboard.html')


@voter_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'voter':
        abort(403)
    return render_template('voter/dashboard.html')

@web_auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.full_name if current_user.is_authenticated else "User"
    logout_user()
    flash(f'{name} logged out successfully.', 'info')
    return redirect(url_for('web_auth.login'))



@voter_bp.route('/dashboard')
@login_required
def dashboard():
    elections = Election.query.filter(Election.end_date >= datetime.utcnow()).all()
    votes = Vote.query.filter_by(voter_id=current_user.id).all()
    
    # You might need to enrich vote records with candidate/position/election info
    vote_records = [{
        "candidate_name": Candidate.query.get(vote.candidate_id).full_name,
        "position_name": Position.query.get(vote.position_id).name,
        "election_title": Election.query.get(vote.election_id).title,
        "voted_at": vote.voted_at.strftime("%Y-%m-%d %H:%M")
    } for vote in votes]

    return render_template('voter/dashboard.html', elections=elections, votes=vote_records)



