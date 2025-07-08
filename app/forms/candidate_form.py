# app/forms/candidate_form.py

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, HiddenField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Optional
from app.models import Candidate
from sqlalchemy import func

class CandidateForm(FlaskForm):
    full_name  = StringField("Full Name", validators=[DataRequired()])
    party_name = StringField("Party (optional)", validators=[Optional()])
    manifesto  = TextAreaField("Manifesto")  # Required only for new candidates
    position   = SelectField(
        "Position",
        choices=[
            ("President", "President"),
            ("Governor", "Governor"),
            ("Senator", "Senator"),
            ("Women Representative", "Women Representative"),
            ("Member Of Parliament", "Member Of Parliament"),
            ("Member Of County Assembly", "Member Of County Assembly"),
        ],
        validators=[DataRequired()]
    )
    candidate_id = HiddenField()
    election_id  = HiddenField()
    submit = SubmitField("Submit Candidate")

    def __init__(self, *args, original_candidate=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_candidate = original_candidate
        if original_candidate:
            self.candidate_id.data = str(original_candidate.id)
            self.election_id.data = str(original_candidate.election_id)

    def validate_full_name(self, field):
        normalized = field.data.strip().lower()
        if not normalized:
            raise ValidationError("Full name is required.")

        query = Candidate.query.filter(
            func.lower(func.trim(Candidate.full_name)) == normalized
        )

        if self.original_candidate:
            query = query.filter(Candidate.id != self.original_candidate.id)
            query = query.filter(
                Candidate.election_id == self.original_candidate.election_id)
        elif self.election_id.data:
            query = query.filter(
                Candidate.election_id == int(self.election_id.data))

        if query.first():
            raise ValidationError(
                "A candidate with this name already exists in this election."
            )

    def validate_manifesto(self, field):
        if not self.original_candidate and not (field.data or "").strip():
            raise ValidationError("Manifesto is required.")
