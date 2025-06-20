from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Notification

voter_bp = Blueprint('voter', __name__)

@voter_bp.route('/notifications')
@login_required
def user_notifications():
    notifs = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    return render_template('voter/notifications.html', notifications=notifs)
