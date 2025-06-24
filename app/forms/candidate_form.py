from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError
from app.models import Candidate

class CandidateForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    party_name = StringField('Party (optional)')
    position = SelectField(
            'Position',
            choices=[
                ('President', 'President'),
                ('Governor', 'Governor'),
                ('Senator', 'Senator'),
                ('Women Representative', 'Women Representative'),
                ('Member Of Parliament', 'Member Of Parliament'),
                ('Member Of County Assembly', 'Member Of County Assembly')
            ],
            validators=[DataRequired()]
            )
    submit = SubmitField('Save')

    def validate_full_name(self, field):
        if Candidate.query.filter_by(full_name=field.data).first():
            raise ValidationError("This candidate is already registered.")

