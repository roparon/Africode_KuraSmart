from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
from app.models import Position



class CandidateForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    party = StringField('Party (optional)')
    position = SelectField(
        'Position',
        choices=[
            ('President', 'President'),
            ('Governor', 'Governor'),
            ('Senator', 'Senator'),
            ('MP', 'Member of Parliament'),
            ('MCA', 'Member of County Assembly')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Save')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position.choices = [(p.id, p.name) for p in Position.query.order_by(Position.name).all()]
