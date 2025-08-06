from flask import Blueprint, render_template, flash, url_for, redirect, request, abort
from flask_login import login_required, current_user
from app.models import Notification, Election, Vote, Candidate, Position, Candidate
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import and_
from werkzeug.utils import secure_filename
from app.forms.profile_form import ProfileImageForm
from collections import defaultdict
from app.forms import VoteForm
from app.extensions import db
import os


voter_bp = Blueprint('voter', __name__)



@voter_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def voter_dashboard():
    try:
        now = datetime.utcnow()

        # Fetch elections based on time
        active_elections = Election.query.filter(
            and_(
                Election.start_date <= now,
                Election.end_date >= now,
                Election.is_active.is_(True)
            )
        ).order_by(Election.created_at.desc()).all()

        upcoming_elections = Election.query.filter(
            and_(
                Election.start_date > now,
                Election.is_active.is_(True)
            )
        ).order_by(Election.start_date.asc()).all()

        ended_elections = Election.query.filter(
            Election.end_date < now
        ).order_by(Election.end_date.desc()).all()

        # Format elections with status
        def format_elections(elections, status):
            nairobi = ZoneInfo("Africa/Nairobi")
            return [{
                'id': e.id,
                'title': e.title,
                'start_date': e.start_date.astimezone(nairobi),
                'end_date': e.end_date.astimezone(nairobi),
                'current_status': status,
                'candidates': Candidate.query.filter_by(election_id=e.id).all()
            } for e in elections]

        all_elections = (
            format_elections(active_elections, 'active') +
            format_elections(upcoming_elections, 'pending') +
            format_elections(ended_elections, 'ended')
        )

        # Fetch votes of the logged-in user
        votes = Vote.query.filter_by(voter_id=current_user.id).order_by(Vote.timestamp.desc()).all()

        # Get list of election_ids where user has voted
        voted_election_ids = [vote.election_id for vote in votes]

        # Handle profile image upload
        form = ProfileImageForm()
        if request.method == 'POST' and form.validate_on_submit():
            image_file = form.image.data
            if image_file:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join('app', 'static', 'profile_images')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                current_user.profile_image = f'profile_images/{filename}'
                db.session.commit()
                flash("Profile image updated successfully.", "success")
                return redirect(url_for('voter.voter_dashboard'))

        return render_template(
            'voter/dashboard.html',
            user=current_user,
            all_elections=all_elections,
            voted_election_ids=voted_election_ids,
            votes=votes,  # Pass votes to template
            form=form
        )

    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('main.index'))


@voter_bp.route('/notifications')
@login_required
def user_notifications():
    try:
        notifs = Notification.query \
            .filter_by(user_id=current_user.id) \
            .order_by(Notification.created_at.desc()) \
            .limit(50).all()
        return render_template('voter/notifications.html', notifications=notifs)
    except Exception as e:
        flash(f"Error loading notifications: {str(e)}", "danger")
        return redirect(url_for('voter.voter_dashboard'))  # or another safe fallback view


@voter_bp.route('/notifications/mark_read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    try:
        notif = Notification.query.get_or_404(notif_id)
        if not notif.read:
            notif.read = True
            db.session.commit()
            flash('Notification marked as read.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error marking notification as read: {str(e)}", 'danger')
    return redirect(url_for('voter.user_notifications'))

@voter_bp.route('/delete-notification/<int:notif_id>', methods=['POST'])
@login_required
def delete_notification(notif_id):
    notification = Notification.query.get_or_404(notif_id)
    if notification.user_id != current_user.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('voter.user_notifications'))

    db.session.delete(notification)
    db.session.commit()
    flash("Notification deleted.", "success")
    return redirect(url_for('voter.user_notifications'))


@voter_bp.route('/vote/<int:election_id>', methods=['POST'])
@login_required
def cast_vote(election_id):
    try:
        election = Election.query.get_or_404(election_id)
        now_local = datetime.now(ZoneInfo("Africa/Nairobi"))
        if election.start_date.tzinfo is None:
            start_local = election.start_date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Africa/Nairobi"))
        else:
            start_local = election.start_date.astimezone(ZoneInfo("Africa/Nairobi"))
        if election.end_date.tzinfo is None:
            end_local = election.end_date.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Africa/Nairobi"))
        else:
            end_local = election.end_date.astimezone(ZoneInfo("Africa/Nairobi"))
        print(f"[DEBUG] now_local: {now_local.isoformat()}")
        print(f"[DEBUG] start_local: {start_local.isoformat()}")
        print(f"[DEBUG] end_local: {end_local.isoformat()}")
        print(f"[DEBUG] Raw start_date: {election.start_date} | tzinfo: {election.start_date.tzinfo}")
        if now_local < start_local:
            flash('Voting has not yet started for this election.', 'warning')
            return redirect(url_for('voter.view_election', election_id=election_id))
        if now_local > end_local:
            flash('Voting has ended for this election.', 'danger')
            return redirect(url_for('voter.view_election', election_id=election_id))
        if election.status != 'active':
            flash('Voting is not currently open for this election.', 'warning')
            return redirect(url_for('voter.view_election', election_id=election_id))
        if not current_user.is_verified:
            flash('Your account is not verified for voting.', 'warning')
            return redirect(url_for('voter.view_election', election_id=election_id))
        candidate_id = request.form.get('candidate_id')
        position_id = request.form.get('position_id')
        if not candidate_id or not position_id:
            flash('No candidate or position selected.', 'warning')
            return redirect(url_for('voter.view_election', election_id=election_id))
        existing_vote = Vote.query.filter_by(
            voter_id=current_user.id,
            election_id=election_id,
            position_id=position_id
        ).first()
        if existing_vote:
            flash('ℹ You have already voted for this position in this election.', 'info')
            return redirect(url_for('voter.view_election', election_id=election_id))
        vote = Vote(
            voter_id=current_user.id,
            election_id=election_id,
            candidate_id=candidate_id,
            position_id=position_id,
            timestamp=datetime.utcnow() 
        )
        db.session.add(vote)
        db.session.commit()
        flash('Vote submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting vote: {str(e)}', 'danger')
    return redirect(url_for('voter.view_election', election_id=election_id))

@voter_bp.route('/election/<int:election_id>', methods=['GET', 'POST'])
@login_required
def view_election(election_id):
    election = Election.query.get_or_404(election_id)
    positions = Position.query.filter_by(election_id=election_id).all()
    candidates = Candidate.query.filter_by(election_id=election_id).all()

    # Get all votes by current user in this election
    user_votes = Vote.query.filter_by(voter_id=current_user.id, election_id=election_id).all()
    voted_position_ids = {vote.position_id for vote in user_votes}
    has_voted = bool(user_votes)

    vote_counts = defaultdict(int)
    total_votes_by_position = defaultdict(int)
    for vote in Vote.query.filter_by(election_id=election_id).all():
        vote_counts[vote.candidate_id] += 1
        total_votes_by_position[vote.position_id] += 1

    candidates_with_votes = defaultdict(list)
    for pos in positions:
        pos_candidates = [c for c in candidates if c.position_id == pos.id]
        for c in pos_candidates:
            c.vote_count = vote_counts.get(c.id, 0)
        sorted_candidates = sorted(pos_candidates, key=lambda c: c.vote_count, reverse=True)
        candidates_with_votes[pos.id] = sorted_candidates

    form = VoteForm()

    return render_template(
        'voter/election_details.html',
        election=election,
        positions=positions,
        candidates_with_votes=candidates_with_votes,
        total_votes_by_position=total_votes_by_position,
        voted_position_ids=voted_position_ids,
        has_voted=has_voted,
        form=form
    )


@voter_bp.route('/voting-history')
@login_required
def voting_history():
    print(f"[DEBUG] current_user.id = {current_user.id}")
    print(f"[DEBUG] current_user.email = {current_user.email}")
    print(f"[DEBUG] current_user.is_authenticated = {current_user.is_authenticated}")

    user_votes = (
        Vote.query
        .filter(Vote.voter_id == current_user.id)
        .options(
            db.joinedload(Vote.election),
            db.joinedload(Vote.position),
            db.joinedload(Vote.candidate)
        )
        .order_by(Vote.timestamp.desc())
        .all()
    )

    print(f"[DEBUG] user_votes count = {len(user_votes)}")

    active_elections = Election.query.filter_by(status='active').all()

    return render_template(
        'voter/voting_history.html',
        votes=user_votes,
        active_elections=active_elections
    )



@voter_bp.route('/help')
def help_support():
    return render_template('voter/help_support.html', title="Help & Support - KuraSmart")