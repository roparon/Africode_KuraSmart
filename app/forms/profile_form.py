from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField

class ProfileImageForm(FlaskForm):
    image = FileField('Upload Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Update Image')
