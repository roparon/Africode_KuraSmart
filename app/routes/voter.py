from flask import Blueprint, render_template, flash, url_for, redirect, abort
from flask_login import login_required, current_user
from app.models import Notification, UserRole, Election, Vote, Candidate, Position
from datetime import datetime
from sqlalchemy import and_
from app.extensions import db

voter_bp = Blueprint('voter', __name__)


@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    if current_user.role != UserRole.voter.value:
        abort(403)
    # Load elections that are currently active
    elections = Election.query.filter(
        and_(
            Election.start_date <= datetime.utcnow(),
            Election.end_date >= datetime.utcnow(),
            Election.status == 'active'
        )
    ).all()
    # Load this voter's past votes
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
                           user=current_user,
                           elections=elections,
                           vote_records=vote_records)

@voter_bp.route('/notifications')
@login_required
def user_notifications():
    notifs = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    return render_template('voter/notifications.html', notifications=notifs)


@voter_bp.route('/notifications/mark_read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id).first_or_404()
    if not notif.read:
        notif.read = True
        db.session.commit()
        flash('Notification marked as read.', 'success')
    return redirect(url_for('voter.user_notifications'))

@voter_bp.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete_notification(notif_id):
    notif = Notification.query.filter_by(id=notif_id).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    flash('Notification deleted.', 'warning')
    return redirect(url_for('voter.user_notifications'))