from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, SelectMultipleField, StringField, TextAreaField, validators

# define all classes for flask web forms
class InputForm(FlaskForm):
    title = StringField('Job title:', [validators.Length(max=35)], render_kw={"placeholder": "e.g. Project Manager"})
    title_select = SelectField('Select job title:', choices=[('no data', 'no data')])
    description = TextAreaField('Description text:', render_kw={"placeholder": "e.g. The validation and analysis of information, including the ability to discover and quantify patterns in data  ..."})

    
class SkillForm(FlaskForm):
    autotag = StringField('Select or manually enter skills:', render_kw={"placeholder": "e.g. MS Word"}, id="tag")
    

class RequirementForm(FlaskForm):
    req_text = TextAreaField('Enter additional requirements:', render_kw={"placeholder": "e.g. The validation and analysis of information, including the ability to discover and quantify patterns in data  ..."})
    multiple = SelectMultipleField('Select job requirements:', choices=[('no data', 'no data')])
  
class FeedbackForm(FlaskForm):
    feedback = TextAreaField('Enter user feedback:', render_kw={"placeholder": "e.g. The quality of the matching results were ..."})
    rating = RadioField('Rating:', choices=[
        ('1', 'Bad'), ('2', 'Poor'), ('3', 'Fair'), ('4', 'Good'), ('5', 'Excellent')], default='3')

