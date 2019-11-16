from flask_wtf import Form
from wtforms import StringField, TextAreaField,SelectField,DateField
from wtforms.validators import InputRequired, Length
from wtforms_components import DateRange
from datetime import date

class fileissueform(Form):
	
	issue = SelectField('Issue: ', choices=[(1,'Bug'),(2,'Feature')],render_kw={"class":"form-control"})
	subject = StringField('Subject: ',validators=[InputRequired(),Length(min=1,max=30)],render_kw={"placeholder": "Subject of the issue","class":"form-control","size":"15"})
	description = TextAreaField('Description: ',validators=[InputRequired(),Length(min=1,max=100)],render_kw={"placeholder": "Description of the issue","class":"form-control","size":"15"})
	date = DateField('Due date: ',validators=[InputRequired(), DateRange(min=date.today())],render_kw={"class":"form-control","size":"15","type":"date"})
		
