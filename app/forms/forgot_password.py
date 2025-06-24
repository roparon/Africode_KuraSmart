from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from app.models import User
from wtforms import ValidationError 



class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")
    
    def validate_email(self, email):

        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that email. You must register first.")
