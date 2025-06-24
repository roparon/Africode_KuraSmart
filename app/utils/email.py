from flask_mail import Message
from flask import current_app
from threading import Thread
from flask import url_for
from app import mail


def send_email_async(to, subject, body):
    from app.extensions import mail
    msg = Message(subject=subject,
                  recipients=[to],
                  body=body,
                  sender=current_app.config.get("MAIL_USERNAME"))
    Thread(target=mail.send, args=(msg,)).start()
def send_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg = Message("Password Reset Request",
                  sender="noreply@kurasmart.com",
                  recipients=[user.email])
    msg.body = f"""To reset your password, click the following link:
{reset_url}
If you did not request this, ignore this email.
"""
    mail.send(msg)
