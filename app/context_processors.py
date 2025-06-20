from flask_login import current_user
from app.models import Notification

def inject_unread_notifs():
    if current_user.is_authenticated:
        count = Notification.query.filter_by(read=False).count()
    else:
        count = 0
    return {'unread_count': count}
