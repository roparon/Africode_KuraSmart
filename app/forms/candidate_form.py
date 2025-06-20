from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app.models import Position

class CandidateForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    party = StringField('Party')
    position = SelectField('Position', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position.choices = [(p.id, p.name) for p in Position.query.order_by(Position.name).all()]
