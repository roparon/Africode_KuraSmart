from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.forms import LoginForm, RegistrationForm, ElectionForm
from app.models import User, Election, Candidate, Vote, Position
from app.extensions import db
from app.enums import UserRole
from datetime import datetime, timedelta
from io import StringIO
import csv

# Blueprints
web_auth_bp = Blueprint('web_auth', __name__)
admin_web_bp = Blueprint('admin_web', __name__, url_prefix='/admin')
voter_bp = Blueprint('voter', __name__, url_prefix='/voter')

# -----------------------------------
# Registration, Login, Logout Routes
# -----------------------------------
@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email is already registered.', 'danger')
            return render_template('register.html', form=form)
        user = User(full_name=form.full_name.data, email=form.email.data, role=UserRole.voter.value)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Welcome {user.full_name}! Registration successful.', 'success')
        return redirect(url_for('web_auth.login'))
    return render_template('register.html', form=form)

@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Your account is pending verification by an admin.', 'warning')
                return redirect(url_for('web_auth.login'))
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.is_superadmin or user.role == UserRole.admin.value:
                return redirect(url_for('admin_web.dashboard'))
            return redirect(url_for('voter.voter_dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@web_auth_bp.route('/logout')
@login_required
def logout():
    name = current_user.full_name
    logout_user()
    flash(f'{name}, you have logged out.', 'info')
    return redirect(url_for('web_auth.login'))

# -------------------------
# Admin Dashboard
# -------------------------
@admin_web_bp.route('/dashboard')
@login_required
def dashboard():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)
    return render_template('admin/dashboard.html')

# -------------------------
# Manage Users
# -------------------------
@admin_web_bp.route('/manage-users', methods=['GET'])
@login_required
def manage_users():
    search = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    pagination = query.order_by(User.full_name).paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items

    return render_template('admin/manage_users.html',
                           users=users,
                           pagination=pagination,
                           search=search)

# -------------------------
# Update User Field (name/email)
# -------------------------
@admin_web_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
def update_user_field(user_id):
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        return jsonify({'error': 'Forbidden'}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No JSON payload received'}), 400

    field = data.get('field')
    value = data.get('value')

    if field in ['full_name', 'email']:
        setattr(user, field, value.strip())
        db.session.commit()
        return jsonify({'message': 'Updated'}), 200

    return jsonify({'error': 'Invalid field'}), 400

# -------------------------
# Change User Role
# -------------------------
@admin_web_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not current_user.is_superadmin:
        abort(403)

    user = User.query.get_or_404(user_id)
    role = request.form.get('role')

    # Ensure role is valid
    if role not in [r.value for r in UserRole]:
        flash('Invalid role selected.', 'danger')
        return redirect(url_for('admin_web.manage_users'))

    user.role = role
    db.session.commit()
    flash(f"Role for {user.full_name} updated to {role.title()}.", 'success')
    return redirect(url_for('admin_web.manage_users'))


# Verify User
# -------------------------
@admin_web_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@login_required
def verify_user(user_id):
    if not current_user.is_superadmin:
        abort(403)

    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f"User {user.full_name} has been verified.", "success")
    return redirect(url_for('admin_web.manage_users'))


@login_required
def unverify_user(user_id):
    if not current_user.is_super_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if not user.is_verified:
        flash(f'{user.full_name} is already unverified.', 'info')
    else:
        user.is_verified = False
        db.session.commit()
        flash(f'Verification revoked for {user.full_name}.', 'warning')
    return redirect(url_for('admin_web.manage_users'))



# -------------------------
# Delete Single User
# -------------------------
@admin_web_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_superadmin:
        abort(403)

    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete yourself.", "danger")
        return redirect(url_for('admin_web.manage_users'))

    db.session.delete(user)
    db.session.commit()
    flash(f"Deleted {user.full_name}", "warning")
    return redirect(url_for('admin_web.manage_users'))

# -------------------------
# Bulk Delete Users
# -------------------------
@admin_web_bp.route('/users/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_users():
    if not current_user.is_superadmin:
        abort(403)

    data = request.get_json()
    ids = data.get('user_ids', [])

    users = User.query.filter(User.id.in_(ids)).all()

    for user in users:
        if user.id != current_user.id:
            db.session.delete(user)

    db.session.commit()
    return jsonify({'message': f'{len(users)} user(s) deleted'}), 200

# -------------------------
# Export Users to CSV
# -------------------------
@admin_web_bp.route('/users/export', methods=['GET'])
@login_required
def export_users_csv():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)

    users = User.query.order_by(User.full_name).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Full Name', 'Email', 'Role', 'Verified'])

    for user in users:
        cw.writerow([
            user.id,
            user.full_name,
            user.email,
            user.role,
            'Yes' if user.is_verified else 'No'
        ])

    si.seek(0)
    return send_file(
        StringIO(si.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='users_export.csv'
    )

# -------------------------
# Manage Elections
# -------------------------
@admin_web_bp.route('/manage-elections', methods=['GET', 'POST'])
@login_required
def manage_elections():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)

    form = ElectionForm()
    now = datetime.now()
    current_datetime = now.strftime('%Y-%m-%dT%H:%M')

    if form.validate_on_submit():
        start = form.start_date.data
        end = form.end_date.data

        if start < now:
            flash('Start date must be in the future or now.', 'danger')
        elif end <= start:
            flash('End date must be after start.', 'danger')
        elif (end - start) > timedelta(hours=12):
            flash('Election cannot exceed 12 hours.', 'danger')
        else:
            election = Election(
                title=form.title.data,
                description=form.description.data,
                start_date=start,
                end_date=end
            )
            db.session.add(election)
            db.session.commit()
            flash('Election created.', 'success')
            return redirect(url_for('admin_web.manage_elections'))

    search_title = request.args.get("search_title", "").strip()
    elections = Election.query.filter(Election.title.ilike(f"{search_title}%")) if search_title else Election.query
    elections = elections.order_by(Election.start_date.desc()).all()

    return render_template('admin/manage_elections.html',
                           elections=elections,
                           form=form,
                           current_datetime=current_datetime,
                           search_title=search_title)

# -------------------------
# View Analytics
# -------------------------
@admin_web_bp.route('/analytics')
@login_required
def view_analytics():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)

    total_users = User.query.count()
    total_votes = Vote.query.count()
    total_elections = Election.query.count()

    return render_template('admin/analytics.html',
                           total_users=total_users,
                           total_votes=total_votes,
                           total_elections=total_elections)

# -------------------------
# Voter Dashboard
# -------------------------
@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    if current_user.role != UserRole.voter.value:
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

    return render_template('voter/dashboard.html',
                           elections=elections,
                           votes=vote_records)

# -------------------------
# Edit & Delete Election
# -------------------------
@admin_web_bp.route('/elections/<int:election_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_election(election_id):
    if not current_user.is_superadmin:
        abort(403)

    election = Election.query.get_or_404(election_id)
    form = ElectionForm(obj=election)

    if form.validate_on_submit():
        election.title = form.title.data
        election.description = form.description.data
        election.start_date = form.start_date.data
        election.end_date = form.end_date.data
        db.session.commit()
        flash("Election updated!", "success")
        return redirect(url_for('admin_web.manage_elections'))

    return render_template('admin/edit_election.html', form=form, election=election)

@admin_web_bp.route('/elections/<int:election_id>/delete', methods=['POST'])
@login_required
def delete_election(election_id):
    if not current_user.is_superadmin:
        abort(403)

    election = Election.query.get_or_404(election_id)
    db.session.delete(election)
    db.session.commit()
    flash("Election deleted!", "warning")
    return redirect(url_for('admin_web.manage_elections'))
