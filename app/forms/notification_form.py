from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

class NotificationForm(FlaskForm):
    title = StringField('Subject', validators=[DataRequired(), Length(max=150)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    send_email = BooleanField('Send via Email')
    submit = SubmitField('Send Notification')
