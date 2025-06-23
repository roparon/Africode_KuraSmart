from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

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

