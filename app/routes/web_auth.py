from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, send_file, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.forms import LoginForm, RegistrationForm, ElectionForm, PositionForm, ProfileImageForm, NotificationForm, ResetPasswordForm, ForgotPasswordForm
from app.models import User, Election, Candidate, Vote, Position, Notification, AuditLog
from app.extensions import db
from app.enums import UserRole, ElectionStatusEnum
from datetime import datetime, timedelta
from app.utils.email import send_email_async, send_reset_email
from app.utils.audit_utils import log_action
from app.utils.decorators import superadmin_required
from werkzeug.utils import secure_filename
from collections import defaultdict
from io import StringIO
import csv
import os
# Blueprints
web_auth_bp = Blueprint('web_auth', __name__)
admin_web_bp = Blueprint('admin_web', __name__, url_prefix='/admin')
voter_bp = Blueprint('voter', __name__, url_prefix='/voter')
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
            log_action("Logged in")
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.is_super_admin():
                return redirect(url_for('admin_web.dashboard'))  # adjust as needed
            elif user.is_admin():
                return redirect(url_for('admin_web.dashboard'))
            elif user.is_candidate():
                return redirect(url_for('candidate.dashboard'))
            elif user.is_voter():
                return redirect(url_for('voter.voter_dashboard'))
            else:
                flash("Your account role is not recognized.", "danger")
                return redirect(url_for('web_auth.login'))
        if user:
            log_action("Failed login attempt", target_type="User", target_id=user.id)

        flash('Invalid email or password.', 'danger')

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
@login_required
def dashboard():
    form = ProfileImageForm() 

    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)

    # ✅ Voter statistics
    total_voters = User.query.filter_by(role='voter').count()
    voted_count = db.session.query(Vote.voter_id).distinct().count()
    turnout_percent = round((voted_count / total_voters) * 100, 2) if total_voters else 0

    # ✅ Election status
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

# -------------------------
# Verify/Unverify User
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

@admin_web_bp.route('/users/<int:user_id>/unverify', methods=['POST'])
@login_required
def unverify_user(user_id):
    if not current_user.is_superadmin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if not user.is_verified:
        flash(f'{user.full_name} is already unverified.', 'info')
    else:
        user.is_verified = False
        db.session.commit()
        flash(f'Verification revoked for {user.full_name}.', 'warning')
    return redirect(url_for('admin_web.manage_users'))

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
                end_date=end,
                status=ElectionStatusEnum.INACTIVE
            )
            db.session.add(election)
            db.session.commit()
            flash('Election created and set to INACTIVE.', 'success')
            return redirect(url_for('admin_web.manage_elections'))

    # Auto-update status based on time
    elections = Election.query.all()
    for election in elections:
        if election.status not in [ElectionStatusEnum.ENDED, ElectionStatusEnum.PAUSED]:
            if election.start_date <= now < election.end_date:
                election.status = ElectionStatusEnum.ACTIVE
            elif now >= election.end_date:
                election.status = ElectionStatusEnum.ENDED
    db.session.commit()

    search_title = request.args.get("search_title", "").strip()
    elections = Election.query.filter(Election.title.ilike(f"{search_title}%")) if search_title else Election.query
    elections = elections.order_by(Election.start_date.desc()).all()

    return render_template('admin/manage_elections.html',
                           elections=elections,
                           form=form,
                           current_datetime=current_datetime,
                           search_title=search_title,
                           now=now)

@admin_web_bp.route('/elections/<int:election_id>/activate', methods=['POST'])
@login_required
def activate_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    election = Election.query.get_or_404(election_id)
    if election.status == ElectionStatusEnum.ENDED:
        flash("Cannot activate an ended election.", "danger")
        return redirect(url_for('admin_web.manage_elections'))
    election.status = ElectionStatusEnum.ACTIVE
    db.session.commit()
    flash(f"Election '{election.title}' activated.", "success")
    return redirect(url_for('admin_web.manage_elections'))

@admin_web_bp.route('/elections/<int:election_id>/pause', methods=['POST'])
@login_required
def pause_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    election = Election.query.get_or_404(election_id)
    if election.status == ElectionStatusEnum.ENDED:
        flash("Cannot pause an ended election.", "danger")
        return redirect(url_for('admin_web.manage_elections'))
    election.status = ElectionStatusEnum.PAUSED
    db.session.commit()
    flash(f"Election '{election.title}' paused.", "warning")
    return redirect(url_for('admin_web.manage_elections'))

@admin_web_bp.route('/elections/<int:election_id>/end', methods=['POST'])
@login_required
def end_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    election = Election.query.get_or_404(election_id)
    if election.status == ElectionStatusEnum.ENDED:
        flash("Election is already ended.", "info")
        return redirect(url_for('admin_web.manage_elections'))
    election.status = ElectionStatusEnum.ENDED
    db.session.commit()
    flash(f"Election '{election.title}' ended.", "danger")
    return redirect(url_for('admin_web.manage_elections'))

@admin_web_bp.route('/elections/<int:election_id>/deactivate', methods=['POST'])
@login_required
def deactivate_election(election_id):
    if not current_user.is_superadmin:
        abort(403)
    election = Election.query.get_or_404(election_id)
    if election.status == ElectionStatusEnum.ENDED:
        flash("Cannot deactivate an ended election.", "danger")
        return redirect(url_for('admin_web.manage_elections'))
    election.status = ElectionStatusEnum.INACTIVE
    db.session.commit()
    flash(f"Election '{election.title}' deactivated.", "info")
    return redirect(url_for('admin_web.manage_elections'))


@admin_web_bp.route('/analytics')
@login_required
def view_analytics():
    if not (current_user.is_superadmin or current_user.role == UserRole.admin.value):
        abort(403)

    total_users = User.query.count()
    total_votes = Vote.query.count()
    total_elections = Election.query.count()
    voted_users = db.session.query(Vote.voter_id).distinct().count()
    position_votes_query = (
        db.session.query(Position.name, db.func.count(Vote.id))
        .join(Vote, Vote.position_id == Position.id)
        .group_by(Position.name)
        .all()
    )
    position_data = list(position_votes_query)

    return render_template('admin/analytics.html',
        total_users=total_users,
        total_votes=total_votes,
        total_elections=total_elections,
        voted_users=voted_users,
        position_data=position_data
    )



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
    now = datetime.now()
    if election.status != ElectionStatusEnum.ENDED and now >= election.end_date:
        election.status = ElectionStatusEnum.ENDED
        db.session.commit()

    if form.validate_on_submit():
        election.title = form.title.data
        election.description = form.description.data
        election.start_date = form.start_date.data
        election.end_date = form.end_date.data
        new_status = request.form.get('status')
        if new_status in [e.value for e in ElectionStatusEnum]:
            election.status = ElectionStatusEnum(new_status)
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

@admin_web_bp.route('/election-results')
@login_required
def election_results():
    # Get selected election ID
    election_id = request.args.get('election_id', type=int)
    elections = Election.query.order_by(Election.title).all()
    selected_election = Election.query.get(election_id) if election_id else elections[0]
    # Gather results
    vote_counts = defaultdict(int)
    candidates = Candidate.query.filter_by(election_id=selected_election.id).all()
    for vote in Vote.query.filter_by(election_id=selected_election.id).all():
        vote_counts[vote.candidate_id] += 1

    labels = [c.full_name for c in candidates]
    counts = [vote_counts.get(c.id, 0) for c in candidates]

    return render_template('admin/election_results.html',
                           elections=elections,
                           selected_election=selected_election,
                           labels=labels,
                           counts=counts)

@admin_web_bp.route('/positions', methods=['GET', 'POST'])
@login_required
def manage_positions():
    if current_user.role != 'admin':
        abort(403)

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
        return redirect(url_for('admin.manage_positions'))

    positions = Position.query.all()
    return render_template('admin/positions.html', form=form, positions=positions)


@admin_web_bp.route('/positions/delete/<int:position_id>', methods=['POST'])
@login_required
def delete_position(position_id):
    if current_user.role != 'admin':
        abort(403)

    position = Position.query.get_or_404(position_id)
    db.session.delete(position)
    db.session.commit()
    flash('Position deleted.', 'info')
    return redirect(url_for('admin_web.manage_positions'))


@admin_web_bp.route('/update-profile-image', methods=['POST'])
@login_required
def update_profile_image():
    form = ProfileImageForm()
    if form.validate_on_submit():
        image_file = request.files.get('image')
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static', 'img', filename)
            image_file.save(image_path)
            current_user.profile_image_url = f"img/{filename}"
            db.session.commit()
            flash("Profile image updated successfully!", "success")
        else:
            flash("Please select a valid image file.", "warning")
    return redirect(url_for('admin_web.dashboard'))


@admin_web_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def manage_notifications():
    if not current_user.is_superadmin:
        abort(403)

    form = NotificationForm()
    if form.validate_on_submit():
        subject = form.title.data
        message = form.message.data
        send_email = form.send_email.data

        notif = Notification(subject=subject, message=message, send_email=send_email)
        db.session.add(notif)
        db.session.commit()

        if send_email:
            users = User.query.all()
            for u in users:
                send_email_async(u.email, subject, message)

        flash('Notification sent successfully!', 'success')
        return redirect(url_for('admin_web.manage_notifications'))

    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', form=form, notifications=notifications)

@admin_web_bp.route('/notifications/edit/<int:notif_id>', methods=['GET', 'POST'])
@login_required
def edit_notification(notif_id):
    if not current_user.is_superadmin:
        abort(403)
    notif = Notification.query.get_or_404(notif_id)
    form = NotificationForm(obj=notif)
    form.id = notif.id  # hidden field

    if form.validate_on_submit():
        notif.subject = form.title.data
        notif.message = form.message.data
        notif.send_email = form.send_email.data
        db.session.commit()
        flash('Notification updated.', 'success')
        return redirect(url_for('admin_web.manage_notifications'))

    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', form=form, notifications=notifications)

@admin_web_bp.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete_notification(notif_id):
    if not current_user.is_superadmin:
        abort(403)
    notif = Notification.query.get_or_404(notif_id)
    db.session.delete(notif)
    db.session.commit()
    flash('Notification deleted.', 'warning')
    return redirect(url_for('admin_web.manage_notifications'))
from app.forms.candidate_form import CandidateForm
# Helper: Get or create position ID
def get_position_id(position_name, election_id):
    position = Position.query.filter_by(name=position_name, election_id=election_id).first()
    if not position:
        position = Position(name=position_name, election_id=election_id)
        db.session.add(position)
        db.session.commit()
    return position.id
# View all candidates
@admin_web_bp.route('/candidates', methods=['GET', 'POST'])
@login_required
def manage_candidates():
    form = CandidateForm()

    # If submitted from modal
    if form.validate_on_submit():
        if not current_user.is_superadmin:
            abort(403)

        position_name = form.position.data
        position_obj = Position.query.filter_by(name=position_name).first()
        if not position_obj:
            flash("Selected position does not exist.", "danger")
        else:
            candidate = Candidate(
                full_name=form.full_name.data,
                party_name=form.party_name.data,
                position=position_name,
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


# Edit candidate
@admin_web_bp.route('/candidates/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_candidate(id):
    candidate = Candidate.query.get_or_404(id)

    if not current_user.is_superadmin:
        abort(403)

    form = CandidateForm(obj=candidate, original_candidate=candidate)
    positions = Position.query.filter_by(election_id=candidate.election_id).all()
    form.position.choices = [(p.name, p.name) for p in positions]

    if form.validate_on_submit():
        normalized_input = form.full_name.data.strip().lower()
        current_name_normalized = candidate.full_name.strip().lower()

        if normalized_input != current_name_normalized:
            existing = Candidate.query.filter(
                db.func.lower(db.func.trim(Candidate.full_name)) == normalized_input
            ).first()
            if existing:
                flash("Another candidate with this name already exists.", "danger")
                return render_template("admin/edit_candidate.html", form=form, candidate=candidate)
        candidate.full_name = form.full_name.data.strip().title()
        candidate.party_name = form.party_name.data.strip() if form.party_name.data else None
        candidate.position = form.position.data
        candidate.position_id = get_position_id(form.position.data, candidate.election_id)
        candidate.manifesto = form.manifesto.data.strip() if form.manifesto.data else None

        db.session.commit()
        flash(f"Candidate {candidate.full_name} for {candidate.position} updated successfully!", "success")
        return redirect(url_for('admin_web.manage_candidates'))

    return render_template("admin/edit_candidate.html", form=form, candidate=candidate)


@admin_web_bp.route('/audit-logs')
@login_required
@superadmin_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)

# Delete candidate
@admin_web_bp.route('/candidates/delete/<int:candidate_id>', methods=['POST'])
@login_required
def delete_candidate(candidate_id):
    if not current_user.is_superadmin:
        abort(403)
    candidate = Candidate.query.get_or_404(candidate_id)
    db.session.delete(candidate)
    db.session.commit()
    flash(f'Candidate {candidate.full_name} for {candidate.position} deleted successfully.', 'warning')
    return redirect(url_for('admin_web.manage_candidates'))