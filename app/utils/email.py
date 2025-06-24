from flask_mail import Message
from flask import current_app, url_for
from threading import Thread
from itsdangerous import URLSafeTimedSerializer as Serializer
from app.models import User
from app.extensions import mail


def send_email_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print("EMAIL SEND ERROR:", e)


def send_email(to, subject, body):
    app = current_app._get_current_object()
    msg = Message(
        subject=subject,
        recipients=[to],
        body=body,
        sender=app.config.get("MAIL_DEFAULT_SENDER")
    )
    Thread(target=send_email_async, args=(app, msg)).start()


def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('web_auth.reset_password', token=token, _external=True)
    subject = "Password Reset Request - KuraSmart"
    body = f"""Hi {user.full_name},

To reset your password, click the link below:
{reset_url}

If you did not request this, please ignore this email.

Regards,
KuraSmart Team
"""
    send_email(user.email, subject, body)


# These functions are better placed in your User model
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
