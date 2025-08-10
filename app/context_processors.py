from flask_login import current_user
from app.models import Notification

def inject_unread_notifs():
    if current_user.is_authenticated:
        count = Notification.query.filter_by(read=False).count()
    else:
        count = 0
    return {'unread_count': count}


from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask

app = Flask(__name__)

@app.context_processor
def inject_now():
    """Make Nairobi time available in all templates as 'now'."""
    return {
        'now': datetime.now(ZoneInfo("Africa/Nairobi"))
    }


from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask

app = Flask(__name__)

@app.context_processor
def utility_processor():
    def to_nairobi(dt):
        if dt is None:
            return None
        return dt.astimezone(ZoneInfo("Africa/Nairobi"))
    return dict(to_nairobi=to_nairobi)
