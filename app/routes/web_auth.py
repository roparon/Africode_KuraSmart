from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.candidate_form import CandidateForm
from app.forms.forms import LoginForm, RegistrationForm, ElectionForm, PositionForm, ProfileImageForm, NotificationForm, ResetPasswordForm, ForgotPasswordForm
from app.models import User, Election, Candidate, Vote, Position, Notification, AuditLog
from app.extensions import db
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.enums import UserRole, ElectionStatusEnum
from datetime import datetime, timedelta
from app.utils.email import send_email, send_reset_email
from app.utils.audit_utils import log_action
from app.utils.decorators import super_admin_required
from werkzeug.utils import secure_filename
from collections import defaultdict
from flask_wtf.csrf import validate_csrf, CSRFError
from app.utils.decorators import admin_required
from io import StringIO
import csv
import os


# Blueprints
web_auth_bp = Blueprint('web_auth', __name__)
admin_web_bp = Blueprint('admin_web', __name__, url_prefix='/admin')
voter_bp = Blueprint('voter', __name__, url_prefix='/voter')


@web_auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            voting_type = form.voting_type.data.lower()
            email = form.email.data.strip()
            full_name = form.full_name.data.strip() if form.full_name.data else ''
            username = form.username.data.strip() if form.username.data else ''
            national_id = form.national_id.data.strip() if form.national_id.data else ''

            if User.query.filter_by(email=email).first():
                flash('Email is already registered.', 'danger')
                return render_template('register.html', form=form)

            if voting_type == 'formal':
                if User.query.filter_by(national_id=national_id).first():
                    flash('This National ID is already registered.', 'danger')
                    return render_template('register.html', form=form)

                user = User(
                    full_name=full_name,
                    email=email,
                    national_id=national_id,
                    dob=form.dob.data,
                    gender=form.gender.data,
                    county=form.county.data,
                    sub_county=form.sub_county.data,
                    division=form.division.data,
                    location=form.location.data,
                    sub_location=form.sub_location.data,
                    voting_type='formal',
                    role=UserRole.voter.value,
                    is_verified=True
                )
            else:
                if User.query.filter_by(username=username).first():
                    flash('Username is already taken.', 'danger')
                    return render_template('register.html', form=form)

                user = User(
                    full_name=full_name,
                    email=email,
                    username=username,
                    voting_type='informal',
                    role=UserRole.voter.value,
                    is_verified=True
                )

            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f"Registration successful for {user.full_name or user.username}!", 'success')
            if user.role in [UserRole.admin.value, UserRole.candidate.value]:
                flash("Your account is pending admin approval.", "info")
            return redirect(url_for('web_auth.login'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration failed: {e}")
            flash("An error occurred during registration. Please try again.", "danger")

    return render_template('register.html', form=form)



@web_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            identifier = form.identifier.data.strip()
            password = form.password.data
            user = User.query.filter(
                (User.email == identifier) | (User.username == identifier)
            ).first()
            if user and user.check_password(password):
                if user.voting_type == 'formal' and not user.is_verified:
                    flash('Your formal voter account is pending verification.', 'warning')
                    return redirect(url_for('web_auth.login'))
                login_user(user, remember=form.remember.data)
                log_action("Logged in", target_type="User", target_id=user.id)
                flash(f"Welcome, {user.full_name}!", 'success')
                if user.is_super_admin():
                    return redirect(url_for('admin_web.dashboard'))
                elif user.is_admin():
                    return redirect(url_for('admin_web.dashboard'))
                elif user.is_candidate():
                    return redirect(url_for('candidate.dashboard'))
                elif user.is_voter():
                    return redirect(url_for('voter.voter_dashboard'))
                else:
                    flash("Your role is not recognized.", "danger")
                    return redirect(url_for('web_auth.login'))
            else:
                if user:
                    log_action("Failed login attempt", target_type="User", target_id=user.id)
                flash('Incorrect credentials. Please try again.', 'danger')
        except Exception as e:
            current_app.logger.error(f"Login error: {e}")
            flash("An unexpected error occurred. Please try again.", "danger")
    return render_template('login.html', form=form)


@web_auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash("If that email is registered, instructions have been sent.", "info")
        return redirect(url_for('web_auth.login'))
    return render_template('forgot_password.html', form=form)

@web_auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for('web_auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for('web_auth.login'))

    return render_template('reset_password.html', form=form, token=token)


@web_auth_bp.route('/logout')
@login_required
def logout():
    log_action("Logged out")
    name = current_user.full_name
    logout_user()
    flash(f'{name}, you have logged out.', 'info')
    return redirect(url_for('web_auth.login'))

# -------------------------
# Admin Dashboard
# -------------------------
@admin_web_bp.route('/dashboard')
def dashboard():
    form = ProfileImageForm()

    if current_user.is_super_admin or current_user.role == UserRole.admin.value:
        try:
            total_voters = User.query.filter_by(role='voter').count()
            voted_count = db.session.query(Vote.voter_id).distinct().count()
            turnout_percent = round((voted_count / total_voters) * 100, 2) if total_voters else 0

            ongoing_elections = Election.query.filter(Election.status == 'active').all()
            ending_soon = [
                e for e in ongoing_elections
                if e.end_date and e.end_date <= datetime.utcnow() + timedelta(hours=4)
            ]

            return render_template(
                'admin/dashboard.html',
                form=form,
                total_voters=total_voters,
                voted_count=voted_count,
                turnout_percent=turnout_percent,
                ongoing_elections=ongoing_elections,
                ending_soon=ending_soon
            )

        except Exception as e:
            current_app.logger.error(f"Admin dashboard error: {e}")
            flash("Error loading dashboard data.", "danger")
            return redirect(url_for('web_auth.login'))

    elif current_user.role == UserRole.voter.value:
        return render_template('voter/dashboard.html')
    else:
        abort(403)

# Manage Users
# -------------------------
@admin_web_bp.route('/manage-users', methods=['GET'])
@login_required
def manage_users():
    search = request.args.get('search', '', type=str)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    try:
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
    except Exception as e:
        current_app.logger.error(f"Manage users error: {e}")
        flash("Unable to load users.", "danger")
        return redirect(url_for('admin_web.dashboard'))


# Update User Field (name/email)
@admin_web_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
def update_user_field(user_id):
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        return jsonify({'error': 'Forbidden'}), 403

    try:
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
    except Exception as e:
        current_app.logger.error(f"Error updating user field: {e}")
        return jsonify({'error': 'Server error'}), 500


# Change User Role
@admin_web_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not current_user.is_superadmin:
        abort(403)

    try:
        user = User.query.get_or_404(user_id)
        role = request.form.get('role')

        if role not in [r.value for r in UserRole]:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('admin_web.manage_users'))

        user.role = role
        db.session.commit()
        flash(f"Role for {user.full_name} updated to {role.title()}.", 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update user role: {e}")
        flash("Could not update user role. Please try again.", "danger")
    return redirect(url_for('admin_web.manage_users'))

# -------------------------
# Verify/Unverify User
# -------------------------
@admin_web_bp.route('/users/<int:user_id>/verify', methods=['POST'])
@login_required
def verify_user(user_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        user = User.query.get_or_404(user_id)
        user.is_verified = True
        db.session.commit()
        flash(f"User {user.full_name} has been verified.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to verify user: {e}")
        flash("Verification failed. Please try again.", "danger")
    return redirect(url_for('admin_web.manage_users'))


@admin_web_bp.route('/pending-users')
@login_required
def pending_users():
    if not current_user.is_admin() and not current_user.is_super_admin():
        abort(403)
    users = User.query.filter(
        User.is_verified == False,
        User.role.in_(['admin', 'candidate'])
    ).order_by(User.full_name).all()
    return render_template('admin/pending_users.html', users=users)


@admin_web_bp.route('/users/<int:user_id>/unverify', methods=['POST'])
@login_required
def unverify_user(user_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        user = User.query.get_or_404(user_id)
        if not user.is_verified:
            flash(f'{user.full_name} is already unverified.', 'info')
        else:
            user.is_verified = False
            db.session.commit()
            flash(f'Verification revoked for {user.full_name}.', 'warning')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to unverify user: {e}")
        flash("Could not unverify user.", "danger")
    return redirect(url_for('admin_web.manage_users'))

# Delete Single User
# -------------------------
@admin_web_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash("You cannot delete yourself.", "danger")
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f"Deleted {user.full_name}", "warning")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete user {user_id}: {e}")
        flash("Failed to delete user. Please try again.", "danger")
    return redirect(url_for('admin_web.manage_users'))

# Bulk Delete Users
@admin_web_bp.route('/users/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_users():
    if not current_user.is_superadmin:
        abort(403)
    try:
        data = request.get_json()
        ids = data.get('user_ids', [])
        users = User.query.filter(User.id.in_(ids)).all()
        for user in users:
            if user.id != current_user.id:
                db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'{len(users)} user(s) deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete users', 'details': str(e)}), 500


# Export Users to CSV

@admin_web_bp.route('/users/export', methods=['GET'])
@login_required
def export_users_csv():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)
    try:
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
    except Exception as e:
        return jsonify({'error': 'Failed to export users', 'details': str(e)}), 500
    
import uuid

UPLOAD_FOLDER = 'static/uploads/candidates'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_candidate_photo(file):
    if file and file.filename:
        ext = file.filename.rsplit('.', 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            file.save(path)
        except Exception as e:
            return None
        return filename
    return None


@admin_web_bp.route('/manage-elections', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_elections():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)

    form = ElectionForm()
    now = datetime.now()
    current_datetime = now.strftime('%Y-%m-%dT%H:%M')
    try:
        if request.method == "POST" and form.validate_on_submit():
            election = Election.query.filter_by(title=form.title.data).first()
            if not election:
                election = Election(
                    title=form.title.data,
                    description=form.description.data,
                    start_date=form.start_date.data,
                    end_date=form.end_date.data,
                    status=form.status.data
                )
                db.session.add(election)
                db.session.commit()
            else:
                election.description = form.description.data
                election.start_date = form.start_date.data
                election.end_date = form.end_date.data
                election.status = form.status.data
            for cand_form in form.candidates.entries:
                full_name = cand_form.form.full_name.data.strip()
                position_name = cand_form.form.position.data
                position = Position.query.filter_by(name=position_name).first()
                if not position:
                    flash(f"Position '{position_name}' does not exist. Please create it first.", "danger")
                    continue
                existing = Candidate.query.filter_by(
                    user_id=current_user.id,
                    election_id=election.id,
                    position_id=position.id
                ).first()
                photo_file = cand_form.form.profile_photo.data
                photo_filename = None
                print(f"DEBUG: photo_file={photo_file}, filename={getattr(photo_file, 'filename', None)}")

                if photo_file and hasattr(photo_file, 'filename') and photo_file.filename:
                    print(f"DEBUG: Candidate form has photo file: {photo_file.filename}")
                    photo_filename = save_candidate_photo(photo_file)
                    print(f"DEBUG: Photo filename assigned: {photo_filename}")
                else:
                    print("DEBUG: No photo file provided for candidate.")

                if cand_form.form.original_candidate:
                    candidate = cand_form.form.original_candidate
                    candidate.full_name = full_name
                    candidate.party_name = cand_form.form.party_name.data
                    candidate.manifesto = cand_form.form.manifesto.data
                    candidate.position = position.name
                    candidate.position_id = position.id
                    if photo_filename:
                        print(f"DEBUG: Updating candidate {candidate.id} profile_photo to {photo_filename}")
                        candidate.profile_photo = photo_filename  
                elif not existing:
                    print(f"DEBUG: Creating new candidate with photo {photo_filename}")
                    candidate = Candidate(
                        full_name=full_name,
                        party_name=cand_form.form.party_name.data,
                        manifesto=cand_form.form.manifesto.data,
                        position=position.name,
                        position_id=position.id,
                        election_id=election.id,
                        user_id=current_user.id,
                        profile_photo=photo_filename
                    )
                    db.session.add(candidate)
                else:
                    print(f"DEBUG: Candidate already exists for position {position.name}")
                    flash(f"⚠️ You are already registered as a candidate for '{position.name}' in this election.", "warning")

            try:
                db.session.commit()
                flash("✅ Election and candidates saved successfully.", "success")
            except IntegrityError:
                db.session.rollback()
                flash("⚠️ Integrity error: You may already be registered as a candidate for this position.", "warning")
            except Exception as db_error:
                db.session.rollback()
                flash(f"❌ Unexpected database error: {db_error}", "danger")

            return redirect(url_for("admin_web.manage_elections"))

        elif request.method == "GET" and request.args.get("edit"):
            election_id = request.args.get("edit")
            election = Election.query.get_or_404(election_id)
            form = ElectionForm(obj=election)
            form.status.data = election.status.value
            form.candidates.entries.clear()
            for candidate in election.candidates:
                cand_form = CandidateForm(
                    obj=candidate,
                    original_candidate=candidate
                )
                form.candidates.append_entry(cand_form)

        # Auto-update election status
        elections = Election.query.all()
        for election in elections:
            if election.status not in [ElectionStatusEnum.ENDED, ElectionStatusEnum.PAUSED]:
                if election.start_date <= now < election.end_date:
                    election.status = ElectionStatusEnum.ACTIVE
                elif now >= election.end_date:
                    election.status = ElectionStatusEnum.ENDED
        db.session.commit()

        # Search functionality
        search_title = request.args.get("search_title", "").strip()
        elections_query = Election.query
        if search_title:
            elections_query = elections_query.filter(Election.title.ilike(f"{search_title}%"))
        elections = elections_query.order_by(Election.start_date.desc()).all()

        return render_template(
            "admin/manage_elections.html",
            elections=elections,
            form=form,
            current_datetime=current_datetime,
            search_title=search_title,
            now=now
        )

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error managing elections: {e}", "danger")
        return redirect(url_for("admin_web.dashboard"))

@admin_web_bp.route('/elections/<int:election_id>/activate', methods=['POST'])
@login_required
def activate_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        election = Election.query.get_or_404(election_id)
        if election.status == ElectionStatusEnum.ENDED:
            flash("Cannot activate an ended election.", "danger")
        else:
            election.status = ElectionStatusEnum.ACTIVE
            db.session.commit()
            flash(f"Election '{election.title}' activated.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error activating election: {e}", "danger")
    return redirect(url_for('admin_web.manage_elections'))


@admin_web_bp.route('/elections/<int:election_id>/pause', methods=['POST'])
@login_required
def pause_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        election = Election.query.get_or_404(election_id)
        if election.status == ElectionStatusEnum.ENDED:
            flash("Cannot pause an ended election.", "danger")
        else:
            election.status = ElectionStatusEnum.PAUSED
            db.session.commit()
            flash(f"Election '{election.title}' paused.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error pausing election: {e}", "danger")
    return redirect(url_for('admin_web.manage_elections'))

@admin_web_bp.route('/elections/<int:election_id>/end', methods=['POST'])
@login_required
def end_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        election = Election.query.get_or_404(election_id)
        if election.status == ElectionStatusEnum.ENDED:
            flash("Election is already ended.", "info")
        else:
            election.status = ElectionStatusEnum.ENDED
            db.session.commit()
            flash(f"Election '{election.title}' ended.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error ending election: {e}", "danger")
    return redirect(url_for('admin_web.manage_elections'))

@admin_web_bp.route('/elections/<int:election_id>/deactivate', methods=['POST'])
@login_required
def deactivate_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        election = Election.query.get_or_404(election_id)
        if election.status == ElectionStatusEnum.ENDED:
            flash("Cannot deactivate an ended election.", "danger")
        else:
            election.status = ElectionStatusEnum.INACTIVE
            db.session.commit()
            flash(f"Election '{election.title}' deactivated.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deactivating election: {e}", "danger")
    return redirect(url_for('admin_web.manage_elections'))


@admin_web_bp.route("/elections/<int:election_id>")
def view_election(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    vote_counts = (
        db.session.query(Vote.candidate_id, func.count(Vote.id).label("vote_count"))
        .filter(Vote.election_id == election_id)
        .group_by(Vote.candidate_id)
        .all()
    )
    vote_count_map = {cid: count for cid, count in vote_counts}
    for candidate in candidates:
        candidate.vote_count = vote_count_map.get(candidate.id, 0)
    total_votes = sum(vote_count_map.values())
    return render_template(
        "admin/view_election.html",
        election=election,
        candidates=candidates,
        total_votes=total_votes,
    )




@admin_web_bp.route('/analytics')
@login_required
def view_analytics():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)
    try:
        total_users = User.query.count()
        total_votes = Vote.query.count()
        total_elections = Election.query.count()
        voted_users = db.session.query(Vote.voter_id).distinct().count()
        position_votes = (
            db.session.query(Position.name, db.func.count(Vote.id))
            .join(Vote, Vote.position_id == Position.id)
            .group_by(Position.name)
            .all()
        )
        return render_template('admin/analytics.html',
                               total_users=total_users,
                               total_votes=total_votes,
                               total_elections=total_elections,
                               voted_users=voted_users,
                               position_data=list(position_votes))
    except Exception as e:
        flash(f"Error loading analytics: {e}", "danger")
        return redirect(url_for('admin_web.dashboard'))



@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    try:
        now = datetime.utcnow()
        all_elections = Election.query.order_by(Election.start_date.desc()).all()
        votes = Vote.query.filter_by(voter_id=current_user.id).all()
        voted_election_ids = {vote.election_id for vote in votes}
        vote_records = []
        for vote in votes:
            candidate = Candidate.query.get(vote.candidate_id)
            position = Position.query.get(vote.position_id)
            election = Election.query.get(vote.election_id)
            vote_records.append({
                "candidate_name": candidate.full_name if candidate else "Unknown",
                "position_name": position.name if position else "Unknown",
                "election_title": election.title if election else "Unknown",
                "voted_at": vote.created_at.strftime("%Y-%m-%d %H:%M")
            })
        return render_template(
            'voter/dashboard.html',
            all_elections=all_elections,
            user=current_user,
            votes=vote_records,
            voted_election_ids=voted_election_ids,
            now=now
        )
    except Exception as e:
        current_app.logger.error(f"Voter dashboard error: {str(e)}")
        flash("Error loading dashboard. Please try again.", "danger")
        return redirect(url_for('main.index'))
    

from app.utils.voting import check_if_user_has_voted
@voter_bp.route('/election/<int:election_id>')
def election_detail(election_id):
    election = Election.query.get_or_404(election_id)
    positions = Position.query.filter_by(election_id=election.id).all()
    candidates = Candidate.query.filter(Candidate.position_id.in_([p.id for p in positions])).all()

    return render_template("election_detail.html", 
                           election=election, 
                           positions=positions, 
                           candidates=candidates,
                           has_voted=check_if_user_has_voted(current_user, election.id))

    
@voter_bp.route('/cast_vote/<int:election_id>', methods=['GET', 'POST'])
@login_required
def cast_vote(election_id):
    election = Election.query.get_or_404(election_id)
    positions = Position.query.filter_by(election_id=election_id).all()
    candidates = Candidate.query.filter_by(election_id=election_id, approved=True).all()

    # Add vote counts to each candidate
    for candidate in candidates:
        candidate.vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()

    if request.method == 'POST':
        for position in positions:
            candidate_id = request.form.get(f'position_{position.id}')
            if candidate_id:
                # Check for existing vote
                existing_vote = Vote.query.filter_by(
                    voter_id=current_user.id,
                    election_id=election_id,
                    position_id=position.id
                ).first()
                if not existing_vote:
                    vote = Vote(
                        voter_id=current_user.id,
                        election_id=election_id,
                        candidate_id=int(candidate_id),
                        position_id=position.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(vote)
        db.session.commit()
        flash("Vote successfully cast!", "success")
        return redirect(url_for('voter.cast_vote', election_id=election_id))

    return render_template(
        'voter/election_overview.html',
        election=election,
        positions=positions,
        candidates=candidates
    )



from sqlalchemy import func
from app.models import Candidate, Vote, Position  # adjust if needed

@voter_bp.route('/election/<int:election_id>')
@login_required
def view_election(election_id):
    if current_user.role != UserRole.voter.value:
        abort(403)

    election = Election.query.get_or_404(election_id)

    if election.status not in ['active', 'pending', 'ended']:
        flash("This election is not accessible at the moment.", "warning")
        return redirect(url_for('voter_dashboard'))

    positions = Position.query.filter_by(election_id=election.id).all()

    # ✅ Subquery to count votes per candidate
    vote_counts_subq = (
        db.session.query(
            Vote.candidate_id,
            func.count(Vote.id).label('vote_count')
        )
        .filter(Vote.election_id == election.id)
        .group_by(Vote.candidate_id)
        .subquery()
    )

    # ✅ Join candidates with vote counts
    candidates = (
        db.session.query(Candidate, vote_counts_subq.c.vote_count)
        .filter(Candidate.election_id == election.id)
        .outerjoin(vote_counts_subq, Candidate.id == vote_counts_subq.c.candidate_id)
        .all()
    )

    # ✅ Attach vote count to each candidate
    candidate_list = []
    for candidate, vote_count in candidates:
        candidate.vote_count = vote_count or 0
        candidate_list.append(candidate)

    # ✅ Group candidates by position.id
    candidates_with_votes = {}
    for position in positions:
        candidates_for_position = [
            c for c in candidate_list if c.position_id == position.id
        ]
        candidates_with_votes[position.id] = candidates_for_position

    # Has user already voted
    votes = Vote.query.filter_by(voter_id=current_user.id, election_id=election.id).all()
    has_voted = len(votes) > 0

    return render_template(
        'election_details.html',
        election=election,
        positions=positions,
        candidates_with_votes=candidates_with_votes,
        has_voted=has_voted,
        user=current_user
    )


# @voter_bp.route('/election/<int:election_id>')
# @login_required
# def view_election(election_id):
#     if current_user.role != UserRole.voter.value:
#         abort(403)

#     election = Election.query.get_or_404(election_id)

#     if election.status not in ['active', 'pending', 'ended']:
#         flash("This election is not accessible at the moment.", "warning")
#         return redirect(url_for('voter_dashboard'))

#     positions = Position.query.filter_by(election_id=election.id).all()

#     # Subquery to get vote counts
#     vote_counts = (
#         db.session.query(Vote.candidate_id, func.count(Vote.id).label("vote_count"))
#         .filter(Vote.election_id == election.id)
#         .group_by(Vote.candidate_id)
#         .subquery()
#     )

#     # Join candidates with vote counts
#     candidates_raw = (
#         db.session.query(Candidate, vote_counts.c.vote_count)
#         .filter(Candidate.election_id == election.id)
#         .outerjoin(vote_counts, Candidate.id == vote_counts.c.candidate_id)
#         .all()
#     )

#     # Attach vote count to each candidate
#     candidate_list = []
#     for candidate, vote_count in candidates_raw:
#         candidate.vote_count = vote_count or 0
#         candidate_list.append(candidate)

#     # Group candidates by position
#     candidates_with_votes = {}
#     for position in positions:
#         candidates_for_position = [c for c in candidate_list if c.position_id == position.id]
#         candidates_with_votes[position.id] = candidates_for_position

#     votes = Vote.query.filter_by(voter_id=current_user.id, election_id=election.id).all()
#     has_voted = len(votes) > 0

#     return render_template(
#         "election_details.html",
#         election=election,
#         positions=positions,
#         candidates_with_votes=candidates_with_votes,
#         has_voted=has_voted,
#         user=current_user
#     )



@admin_web_bp.route('/elections/<int:election_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_election(election_id):
    if not current_user.is_superadmin:
        abort(403)

    try:
        election = Election.query.get_or_404(election_id)
        now = datetime.now()

        if election.status != ElectionStatusEnum.ENDED and now >= election.end_date:
            election.status = ElectionStatusEnum.ENDED
            db.session.commit()

        form = ElectionForm()

        # --- On GET: Build form with current candidates ---
        if request.method == "GET":
            form = ElectionForm(obj=election)
            form.candidates.entries = []

            # Load existing candidates into the form
            for candidate in election.candidates:
                entry = form.candidates.append_entry()
                entry.form.original_candidate = candidate
                entry.form.full_name.data = candidate.full_name
                entry.form.party_name.data = candidate.party_name
                entry.form.manifesto.data = candidate.manifesto
                entry.form.position.data = candidate.position
                entry.form.election_id.data = str(election.id)
                entry.form.candidate_id.data = str(candidate.id)

            # Append a new blank candidate entry if requested
            if request.args.get("add_candidate"):
                form.candidates.append_entry()

            # Remove a candidate entry by index if requested
            if request.args.get("remove_candidate"):
                index = int(request.args.get("remove_candidate"))
                if 0 <= index < len(form.candidates.entries):
                    form.candidates.entries.pop(index)

            return render_template("admin/edit_election.html", form=form, election=election)

        # --- On POST: Process form submission ---
        if request.method == "POST":
            form = ElectionForm(request.form)

            # Re-link original_candidate based on form input
            for entry in form.candidates.entries:
                candidate_id = entry.form.candidate_id.data
                if candidate_id:
                    existing = Candidate.query.get(candidate_id)
                    if existing:
                        entry.form.original_candidate = existing
                        entry.form.election_id.data = str(election.id)
                else:
                    entry.form.original_candidate = None
                    entry.form.election_id.data = str(election.id)

            if form.validate_on_submit():
                election.title = form.title.data
                election.description = form.description.data
                election.start_date = form.start_date.data
                election.end_date = form.end_date.data
                election.status = form.status.data

                # Track original candidates by unique (name, position)
                existing_candidates = {
                    (c.full_name.strip().lower(), c.position.strip().lower()): c
                    for c in election.candidates
                }
                seen_keys = set()

                for entry in form.candidates.entries:
                    data = entry.data
                    full_name = (data.get("full_name") or "").strip()
                    position_name = (data.get("position") or "").strip()

                    if not full_name or not position_name:
                        flash("Candidate name and position are required.", "warning")
                        continue

                    key = (full_name.lower(), position_name.lower())
                    seen_keys.add(key)

                    # ✅ Get or create position
                    position = Position.query.filter_by(name=position_name, election_id=election.id).first()
                    if not position:
                        position = Position(name=position_name, election_id=election.id)
                        db.session.add(position)
                        db.session.flush()  # Needed to get position.id

                    # ✅ Update existing candidate
                    if key in existing_candidates:
                        candidate = existing_candidates[key]
                        candidate.party_name = data.get("party_name")
                        candidate.manifesto = data.get("manifesto")
                        candidate.position = position_name
                        candidate.position_id = position.id
                    else:
                        # ✅ Add new candidate
                        new_candidate = Candidate(
                            user_id=current_user.id,
                            election_id=election.id,
                            full_name=full_name,
                            party_name=data.get("party_name"),
                            manifesto=data.get("manifesto"),
                            position=position_name,
                            position_id=position.id
                        )
                        db.session.add(new_candidate)

                # ✅ Remove deleted candidates
                for key, candidate in existing_candidates.items():
                    if key not in seen_keys:
                        db.session.delete(candidate)

                db.session.commit()
                flash("Election updated successfully!", "success")
                return redirect(url_for("admin_web.manage_elections"))

        return render_template("admin/edit_election.html", form=form, election=election)

    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error editing election: {e}", "danger")
        return redirect(url_for("admin_web.manage_elections"))




@admin_web_bp.route('/elections/<int:election_id>/delete', methods=['POST'])
@login_required
def delete_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        election = Election.query.get_or_404(election_id)
        db.session.delete(election)
        db.session.commit()
        flash("Election deleted!", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting election: {e}", "danger")
    return redirect(url_for('admin_web.manage_elections'))


@admin_web_bp.route('/election-results')
@login_required
def election_results():
    try:
        election_id = request.args.get('election_id', type=int)
        elections = Election.query.order_by(Election.title).all()
        selected = Election.query.get(election_id) if election_id else elections[0]

        vote_counts = defaultdict(int)
        candidates = Candidate.query.filter_by(election_id=selected.id).all()
        for vote in Vote.query.filter_by(election_id=selected.id).all():
            vote_counts[vote.candidate_id] += 1

        labels = [c.full_name for c in candidates]
        counts = [vote_counts.get(c.id, 0) for c in candidates]
        return render_template('admin/election_results.html',
                               elections=elections,
                               selected_election=selected,
                               labels=labels,
                               counts=counts)
    except Exception as e:
        flash(f"Error fetching election results: {e}", "danger")
        return redirect(url_for('admin_web.manage_elections'))

@admin_web_bp.route('/positions', methods=['GET', 'POST'])
@login_required
def manage_positions():
    if current_user.role != UserRole.admin.value:
        abort(403)
    try:
        form = PositionForm()
        form.election_id.choices = [(e.id, e.title) for e in Election.query.all()]
        if form.validate_on_submit():
            position = Position(
                name=form.name.data,
                description=form.description.data,
                election_id=form.election_id.data
            )
            db.session.add(position)
            db.session.commit()
            flash('Position created successfully.', 'success')
            return redirect(url_for('admin_web.manage_positions'))
        positions = Position.query.all()
        return render_template('admin/positions.html', form=form, positions=positions)
    except Exception as e:
        db.session.rollback()
        flash(f"Error managing positions: {e}", "danger")
        return redirect(url_for('admin_web.manage_positions'))

@admin_web_bp.route('/positions/delete/<int:position_id>', methods=['POST'])
@login_required
def delete_position(position_id):
    if current_user.role != UserRole.admin.value:
        abort(403)
    try:
        position = Position.query.get_or_404(position_id)
        db.session.delete(position)
        db.session.commit()
        flash('Position deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting position: {e}", "danger")
    return redirect(url_for('admin_web.manage_positions'))



@admin_web_bp.route('/update-profile-image', methods=['POST'])
@login_required
def update_profile_image():
    form = ProfileImageForm()
    try:
        if form.validate_on_submit():
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(current_app.root_path, 'static', 'img', filename)
                image_file.save(image_path)
                current_user.profile_image_url = f"img/{filename}"
                db.session.commit()
                flash("Profile image updated successfully!", "success")
            else:
                flash("Please select a valid image file.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving profile image: {e}", "danger")
    return redirect(url_for('admin_web.dashboard'))

@admin_web_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def manage_notifications():
    if not current_user.is_superadmin:
        abort(403)
    form = NotificationForm()
    try:
        if form.validate_on_submit():
            notif = Notification(
                subject=form.title.data,
                message=form.message.data,
                send_email=form.send_email.data
            )
            db.session.add(notif)
            db.session.commit()
            if form.send_email.data:
                users = User.query.all()
                for u in users:
                    try:
                        send_email(u.email, notif.subject, notif.message)
                    except Exception:
                        current_app.logger.exception(f"Failed email to {u.email}")
            flash('Notification sent successfully!', 'success')
            return redirect(url_for('admin_web.manage_notifications'))
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template('admin/notifications.html', form=form, notifications=notifications)
    except Exception as e:
        db.session.rollback()
        flash(f"Error in notifications: {e}", "danger")
        return redirect(url_for('admin_web.manage_notifications'))

@admin_web_bp.route('/notifications/edit/<int:notif_id>', methods=['GET', 'POST'])
@login_required
def edit_notification(notif_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        notif = Notification.query.get_or_404(notif_id)
        form = NotificationForm(obj=notif)
        if form.validate_on_submit():
            notif.subject = form.title.data
            notif.message = form.message.data
            notif.send_email = form.send_email.data
            db.session.commit()
            flash('Notification updated.', 'success')
            return redirect(url_for('admin_web.manage_notifications'))
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template('admin/notifications.html', form=form, notifications=notifications)
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating notification: {e}", "danger")
        return redirect(url_for('admin_web.manage_notifications'))

@admin_web_bp.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete_notification(notif_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        notif = Notification.query.get_or_404(notif_id)
        db.session.delete(notif)
        db.session.commit()
        flash('Notification deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting notification: {e}", "danger")
    return redirect(url_for('admin_web.manage_notifications'))

# Candidate routes
@admin_web_bp.route('/candidates', methods=['GET', 'POST'])
@login_required
def manage_candidates():
    form = CandidateForm()
    try:
        if form.validate_on_submit():
            if not current_user.is_superadmin:
                abort(403)
            position_obj = Position.query.filter_by(name=form.position.data).first()
            if not position_obj:
                flash("Selected position does not exist.", "danger")
            else:
                candidate = Candidate(
                    full_name=form.full_name.data,
                    party_name=form.party_name.data,
                    position=form.position.data,
                    position_id=position_obj.id,
                    user_id=current_user.id,
                    election_id=position_obj.election_id
                )
                db.session.add(candidate)
                db.session.commit()
                flash("Candidate successfully created.", "success")
                return redirect(url_for('admin_web.manage_candidates'))
        elif request.method == 'POST':
            flash("Form validation failed. Please check your input.", "danger")

        candidates = Candidate.query.all()
        return render_template('admin/candidates.html', candidates=candidates, form=form)

    except Exception as e:
        db.session.rollback()
        import traceback
        print("Exception in /candidates route:", traceback.format_exc())
        flash(f"Error managing candidates: {e}", "danger")
        return render_template('admin/candidates.html', candidates=[], form=form)


def get_position_id(position_name, election_id):
    position = Position.query.filter_by(name=position_name, election_id=election_id).first()
    if not position:
        position = Position(name=position_name, election_id=election_id)
        db.session.add(position)
        db.session.commit()
    return position.id

@admin_web_bp.route('/candidates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_candidate(id):
    candidate = Candidate.query.get_or_404(id)
    if not current_user.is_superadmin:
        abort(403)
    form = CandidateForm(obj=candidate, original_candidate=candidate)
    try:
        form.position.choices = [(p.name, p.name) for p in Position.query.filter_by(election_id=candidate.election_id).all()]
        if form.validate_on_submit():
            normalized = form.full_name.data.strip().lower()
            if normalized != candidate.full_name.strip().lower():
                existing = Candidate.query.filter(db.func.lower(db.func.trim(Candidate.full_name)) == normalized).first()
                if existing:
                    flash("Another candidate with this name already exists.", "danger")
                    return render_template("admin/edit_candidate.html", form=form, candidate=candidate)
            candidate.full_name = form.full_name.data.strip().title()
            candidate.party_name = form.party_name.data.strip() if form.party_name.data else None
            candidate.position = form.position.data
            candidate.position_id = get_position_id(form.position.data, candidate.election_id)
            candidate.manifesto = form.manifesto.data.strip() if form.manifesto.data else None
            db.session.commit()
            flash(f"Candidate {candidate.full_name} updated successfully!", "success")
            return redirect(url_for('admin_web.manage_candidates'))
        return render_template("admin/edit_candidate.html", form=form, candidate=candidate)
    except Exception as e:
        db.session.rollback()
        flash(f"Error editing candidate: {e}", "danger")
        return redirect(url_for('admin_web.manage_candidates'))

@admin_web_bp.route('/audit-logs')
@login_required
@super_admin_required
def audit_logs():
    try:
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
        return render_template('admin/audit_logs.html', logs=logs)
    except Exception as e:
        flash(f"Error loading audit logs: {e}", "danger")
        return redirect(url_for('admin_web.dashboard'))

@admin_web_bp.route('/candidates/delete/<int:candidate_id>', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    if not current_user.is_superadmin:
        abort(403)
    try:
        candidate = Candidate.query.get_or_404(candidate_id)
        db.session.delete(candidate)
        db.session.commit()
        flash(f'Candidate {candidate.full_name} deleted successfully.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting candidate: {e}", "danger")
    return redirect(url_for('admin_web.manage_candidates'))


@admin_web_bp.route('/<action>-user/<int:user_id>', methods=['POST'])
@login_required
def user_action(action, user_id):
    # CSRF protection
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        validate_csrf(csrf_token)
    except CSRFError:
        return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 400

    user = User.query.get_or_404(user_id)

    if action == 'approve':
        user.is_approved = True
        user.is_blocked = False
        db.session.commit()
        return jsonify({'success': True})
    elif action == 'reject':
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    elif action == 'block':
        user.is_blocked = True
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400


@admin_web_bp.route('/approve-all-users', methods=['POST'])
@login_required
def approve_all_users():
    try:
        pending_users = User.query.filter_by(is_approved=False).all()
        for user in pending_users:
            user.is_approved = True
        db.session.commit()
        flash(f'All {len(pending_users)} pending users have been approved.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to approve all users: {e}")
        flash("Approval failed. Please try again.", "danger")

    return redirect(url_for('admin_web.pending_users'))

@admin_web_bp.route('/approve_candidate/<int:candidate_id>', methods=['POST'])
@login_required
def approve_candidate(candidate_id):
    from app.models import Candidate
    candidate = Candidate.query.get_or_404(candidate_id)
    candidate.approved = True
    db.session.commit()
    flash(f"Candidate {candidate.full_name} approved!", "success")
    return redirect(request.referrer or url_for('some_view'))

@admin_web_bp.route('/approve_all_candidates', methods=['POST'])
@login_required
def approve_all_candidates():
    from app.models import Candidate
    Candidate.query.filter_by(approved=False).update({'approved': True})
    db.session.commit()
    flash("All unapproved candidates are now approved!", "success")
    return redirect(request.referrer or url_for('some_view'))

@admin_web_bp.route('/candidate/<int:candidate_id>/unapprove', methods=['POST'])
def reject_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    candidate.approved = False
    db.session.commit()
    flash(f'{candidate.full_name} has been unapproved.', 'warning')
    return redirect(url_for('admin_web.manage_candidates'))

@admin_web_bp.route('/candidates/reject_all', methods=['POST'])
@login_required
def reject_all_candidates():
    if not current_user.is_superadmin:
        abort(403)
    Candidate.query.update({Candidate.approved: False})
    db.session.commit()
    flash("All candidates have been unapproved.", "warning")
    return redirect(url_for('admin_web.manage_candidates'))



