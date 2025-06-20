from datetime import datetime, timedelta
from app.models import Election, Notification, User
from app.extensions import db
from app.utils.email import send_email_async

def send_reminders():
    tomorrow = datetime.utcnow() + timedelta(days=1)
    upcoming = Election.query.filter(
        Election.start_date.between(datetime.utcnow(), tomorrow)
    ).all()

    for election in upcoming:
        subject = f"Reminder: Upcoming Election '{election.title}'"
        msg = f"The election '{election.title}' starts on {election.start_date:%Y-%m-%d %H:%M} UTC."
        notif = Notification(subject=subject, message=msg, send_email=True)
        db.session.add(notif)
        db.session.commit()

        users = User.query.all()
        for u in users:
            send_email_async(u.email, subject, msg)
