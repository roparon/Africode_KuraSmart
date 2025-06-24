from flask_mail import Message
from flask import current_app
from threading import Thread
from flask import url_for
from app.models import User


def send_email_async(to, subject, body):
    from app.extensions import mail
    msg = Message(subject=subject,
                  recipients=[to],
                  body=body,
                  sender=current_app.config.get("MAIL_USERNAME"))
    Thread(target=mail.send, args=(msg,)).start()
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

def get_reset_token(self, expires_sec=1800):
    s = Serializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': self.id})

@staticmethod
def verify_reset_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, max_age=1800)['user_id']
    except Exception:
        return None
    return User.query.get(user_id)

