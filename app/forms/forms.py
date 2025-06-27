from flask_wtf import FlaskForm, csrf
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateTimeLocalField, SelectField,BooleanField, FileField, HiddenField, BooleanField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError,  Email as EmailValidator, Optional
from flask_wtf.file import FileField, FileAllowed
from app.models import User
from datetime import datetime, timedelta


class ProfileImageForm(FlaskForm):
    image = FileField('Upload Profile Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only .jpg, .jpeg, .png allowed')
    ])
    submit = SubmitField('Update Image')


class RegistrationForm(FlaskForm):
    voting_type = SelectField(
        'Voting Type',
        choices=[('formal', 'Formal (National ID required)'), ('informal', 'Informal')],
        validators=[DataRequired()]
    )

    full_name = StringField(
        'Full Name (as on your National ID)',
        validators=[Optional(), Length(min=2, max=100)]
    )
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match')
    ])
    username = StringField('Username', validators=[Optional(), Length(min=3, max=80)])
    national_id = StringField('National ID', validators=[Optional(), Length(min=6, max=20)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')
    ], validators=[Optional()])
    county = StringField('County', validators=[Optional()])
    sub_county = StringField('Sub-county', validators=[Optional()])
    division = StringField('Division', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    sub_location = StringField('Sub-location', validators=[Optional()])
    submit = SubmitField('Register')

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        # Formal voter: full_name must be required
        if self.voting_type.data == 'formal' and not self.full_name.data.strip():
            self.full_name.errors.append("Full name is required for formal voters.")
            return False

        return True


class LoginForm(FlaskForm):
    identifier = StringField('Email or Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def validate_identifier(self, field):
        try:
            EmailValidator()(self, field)
        except ValidationError:
            if len(field.data.strip()) < 3:
                raise ValidationError("Enter a valid email or username.")

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
    id = HiddenField()
    message = TextAreaField('Message', validators=[DataRequired()])
    send_email = BooleanField('Send via Email')
    submit = SubmitField('Send Notification')
    
    def validate_title(self, field):
        if len(field.data) < 5:
            raise ValidationError("Title must be at least 5 characters long.")
        

class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user is None:
            raise ValidationError("There is no account with this email. You must register first.")

class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Reset Password")

        

