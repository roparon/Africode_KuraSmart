from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateTimeLocalField, SelectField,BooleanField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed

from datetime import datetime, timedelta


class ProfileImageForm(FlaskForm):
    image = FileField('Upload Profile Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only .jpg, .jpeg, .png allowed')
    ])
    submit = SubmitField('Update Image')


class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class VerificationRequestForm(FlaskForm):
    submit = SubmitField("Submit Verification Request", validators=[DataRequired()])



class ElectionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    start_date = DateTimeLocalField('Start Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_date = DateTimeLocalField('End Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Create Election')

    def validate_start_date(self, field):
        if field.data < datetime.now():
            raise ValidationError("Start date cannot be in the past.")

    def validate_end_date(self, field):
        if field.data <= self.start_date.data:
            raise ValidationError("End time must be after the start time.")
        elif field.data > self.start_date.data + timedelta(hours=12, minutes=30):
            raise ValidationError("Election duration cannot exceed 12 hours 30 minutes.")
        

class PositionForm(FlaskForm):
    name = StringField('Position Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description')
    election_id = SelectField('Assign to Election', coerce=int)
    submit = SubmitField('Save Position')


class NotificationForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    send_email = BooleanField('Send via Email')
    submit = SubmitField('Send Notification')
    
    def validate_title(self, field):
        if len(field.data) < 5:
            raise ValidationError("Title must be at least 5 characters long.")
        

