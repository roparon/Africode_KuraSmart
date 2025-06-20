from flask_mail import Message
from flask import current_app
from threading import Thread

def send_email_async(to, subject, body):
    from app.extensions import mail  # move inside the function

    msg = Message(subject=subject,
                  recipients=[to],
                  body=body,
                  sender=current_app.config.get("MAIL_USERNAME"))

    Thread(target=mail.send, args=(msg,)).start()
