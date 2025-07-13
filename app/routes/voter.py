from flask import Blueprint, render_template, flash, url_for, redirect, abort, request
from flask_login import login_required, current_user
from app.models import Notification, UserRole, Election, Vote, Candidate, Position
from datetime import datetime
from sqlalchemy import and_
from app.extensions import db

voter_bp = Blueprint('voter', __name__)


@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    try:
        now = datetime.utcnow()

        active_elections = Election.query.filter(
            and_(
                Election.start_date <= now,
                Election.end_date >= now,
                Election.is_active == True
            )
        ).order_by(Election.created_at.desc()).all()

        upcoming_elections = Election.query.filter(
            and_(
                Election.start_date > now,
                Election.is_active == True
            )
        ).order_by(Election.start_date.asc()).all()

        ended_elections = Election.query.filter(
            Election.end_date < now
        ).order_by(Election.end_date.desc()).all()

        all_elections = [
            {
                'id': e.id,
                'title': e.title,
                'start_date': e.start_date,
                'end_date': e.end_date,
                'current_status': 'active'
            } for e in active_elections
        ] + [
            {
                'id': e.id,
                'title': e.title,
                'start_date': e.start_date,
                'end_date': e.end_date,
                'current_status': 'pending'
            } for e in upcoming_elections
        ] + [
            {
                'id': e.id,
                'title': e.title,
                'start_date': e.start_date,
                'end_date': e.end_date,
                'current_status': 'ended'
            } for e in ended_elections
        ]

        return render_template(
            'voter/dashboard.html',
            user=current_user,
            all_elections=all_elections
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
        flash(f"Error marking notification as read: {str(e)}", "danger")
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
        flash(f"Error deleting notification: {str(e)}", "danger")
    return redirect(url_for('voter.user_notifications'))


@voter_bp.route('/vote/<int:election_id>', methods=['POST'])
@login_required
def cast_vote(election_id):
    try:
        election = Election.query.get_or_404(election_id)

        if election.current_status != 'active' or not current_user.is_verified:
            flash('You are not allowed to vote in this election.', 'warning')
            return redirect(url_for('voter.voter_dashboard'))

        # TODO: Implement vote recording logic
        # Example:
        # vote = Vote(user_id=current_user.id, election_id=election_id, candidate_id=request.form.get('candidate_id'))
        # db.session.add(vote)
        # db.session.commit()

        flash('Vote submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting vote: {str(e)}', 'danger')

    return redirect(url_for('voter.voter_dashboard'))
