from flask import Blueprint, render_template, flash, url_for, redirect, request
from flask_login import login_required, current_user
from app.models import Notification, Election, Vote, Candidate, Position
from datetime import datetime
from sqlalchemy import and_
from werkzeug.utils import secure_filename
from app.forms.profile_form import ProfileImageForm
from app.extensions import db
import os


voter_bp = Blueprint('voter', __name__)




  # Adjust path as needed


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
            return [{
                'id': e.id,
                'title': e.title,
                'start_date': e.start_date,
                'end_date': e.end_date,
                'current_status': status
            } for e in elections]

        all_elections = (
            format_elections(active_elections, 'active') +
            format_elections(upcoming_elections, 'pending') +
            format_elections(ended_elections, 'ended')
        )

        # Get voted election IDs for this user
        voted_election_ids = [vote.election_id for vote in Vote.query.filter_by(voter_id=current_user.id).all()]


        # Initialize profile image form
        form = ProfileImageForm()

        # Handle form submission
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

                flash("✅ Profile image updated successfully.", "success")
                return redirect (url_for('voter.voter_dashboard'))

        # ✅ Pass everything needed to template
        return render_template(
            'voter/dashboard.html',
            user=current_user,
            all_elections=all_elections,
            voted_election_ids=voted_election_ids,
            form=form
        )

    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return redirect(url_for('main.index'))


@voter_bp.route('/notifications')
@login_required
def user_notifications():
    try:
        notifs = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
        return render_template('voter/notifications.html', notifications=notifs)
    except Exception as e:
        flash(f"Error loading notifications: {str(e)}", "danger")
        return redirect(url_for('voter.voter_dashboard'))


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


@voter_bp.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete_notification(notif_id):
    try:
        notif = Notification.query.get_or_404(notif_id)
        db.session.delete(notif)
        db.session.commit()
        flash('Notification deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting notification: {str(e)}", 'danger')
    return redirect(url_for('voter.user_notifications'))

@voter_bp.route('/vote/<int:election_id>', methods=['POST'])
@login_required
def cast_vote(election_id):
    try:
        election = Election.query.get_or_404(election_id)

        if election.current_status != 'active':
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
            flash('You have already voted for this position in this election.', 'info')
            return redirect(url_for('voter.view_election', election_id=election_id))
        vote = Vote(
            voter_id=current_user.id,
            election_id=election_id,
            candidate_id=candidate_id,
            position_id=position_id
        )
        db.session.add(vote)
        db.session.commit()

        flash('Vote submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting vote: {str(e)}', 'danger')

    return redirect(url_for('voter.view_election', election_id=election_id))

from collections import defaultdict
@voter_bp.route('/election/<int:election_id>')
@login_required
def view_election(election_id):
    election = Election.query.get_or_404(election_id)
    positions = Position.query.filter_by(election_id=election_id).all()
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    candidate_votes = {
        c.id: Vote.query.filter_by(candidate_id=c.id).count()
        for c in candidates
    }
    for c in candidates:
        c.vote_count = candidate_votes.get(c.id, 0)
    candidates_with_votes = defaultdict(list)
    for pos in positions:
        filtered = [c for c in candidates if c.position_id == pos.id]
        sorted_candidates = sorted(filtered, key=lambda c: c.vote_count, reverse=True)
        candidates_with_votes[pos.id] = sorted_candidates
    return render_template(
        'voter/election_details.html',
        election=election,
        positions=positions,
        candidates_with_votes=candidates_with_votes
    )