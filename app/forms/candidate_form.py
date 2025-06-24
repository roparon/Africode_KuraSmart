from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError
from app.models import Candidate
from sqlalchemy import func


class CandidateForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    party_name = StringField('Party (optional)')
    manifesto = TextAreaField('Manifesto', validators=[DataRequired()])
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

    def __init__(self, original_candidate=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_candidate = original_candidate

    def validate_full_name(self, field):
        normalized_name = field.data.strip().lower()

        existing = Candidate.query.filter(
            func.lower(func.trim(Candidate.full_name)) == normalized_name
        ).first()

        if existing and (not self.original_candidate or existing.id != self.original_candidate.id):
            raise ValidationError("This candidate is already registered.")