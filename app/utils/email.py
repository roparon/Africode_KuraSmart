from flask_mail import Message
from app import mail
from flask import current_app



def send_email_async(recipient, subject, body):
    with current_app.app_context():
        msg = Message(subject=subject,
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[recipient],
                      body=body)
        mail.send(msg)
