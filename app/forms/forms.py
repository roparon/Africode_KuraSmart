from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from datetime import date, timedelta




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
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Create Election')

    def validate_start_date(self, field):
        if field.data < date.today():
            raise ValidationError("Start date cannot be in the past.")

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError("End date must be after the start date.")
        
    def validate_end_date(self, field):
        if field.data <= self.start_date.data:
            raise ValidationError("End time must be after the start time.")
        elif field.data > self.start_date.data + timedelta(hours=12):  # example: 6 hours max
            raise ValidationError("Election duration cannot exceed 12 hours.")
