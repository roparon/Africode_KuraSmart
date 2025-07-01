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

    from datetime import datetime
    from sqlalchemy import and_

    elections = Election.query.filter(
        and_(
            Election.start_date <= datetime.utcnow(),
            Election.end_date >= datetime.utcnow(),
            Election.status == 'active'
        )
    ).all()

    return render_template('voter/dashboard.html', elections=elections, user=current_user)


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