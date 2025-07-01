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
    try:
        now = datetime.utcnow()
        # Active elections: currently running
        active_elections = Election.query.filter(
            and_(
                Election.start_date <= now,
                Election.end_date >= now,
                Election.active == True
            )
        ).order_by(Election.created_at.desc()).all()
        # Upcoming (pending) elections: not started yet
        upcoming_elections = Election.query.filter(
            and_(
                Election.start_date > now,
                Election.active == True
            )
        ).order_by(Election.start_date.asc()).all()
        # Ended elections
        ended_elections = Election.query.filter(
            Election.end_date < now
        ).order_by(Election.end_date.desc()).all()
        return render_template(
            'voter/dashboard.html',
            user=current_user,
            active_elections=active_elections,
            upcoming_elections=upcoming_elections,
            ended_elections=ended_elections
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
        notif = Notification.query.filter_by(id=notif_id).first_or_404()
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
        notif = Notification.query.filter_by(id=notif_id).first_or_404()
        db.session.delete(notif)
        db.session.commit()
        flash('Notification deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting notification: {str(e)}", "danger")
    return redirect(url_for('voter.user_notifications'))
