from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Optional
from app.models import Candidate
from sqlalchemy import func


class CandidateForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    party_name = StringField('Party (optional)', validators=[Optional()])
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

    def __init__(self, *args, original_candidate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_candidate = original_candidate

    def validate_full_name(self, field):
        if not self.original_candidate:
            from app.models import Candidate
            normalized_name = field.data.strip().lower()
            existing = Candidate.query.filter(
                func.lower(func.trim(Candidate.full_name)) == normalized_name
            ).first()
            if existing:
                raise ValidationError("This candidate is already registered.")
