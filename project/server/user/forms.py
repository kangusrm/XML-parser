# project/server/user/forms.py


from flask_wtf import Form
from wtforms import StringField, PasswordField, FileField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(Form):
    email = StringField('Email Address', [DataRequired(), Email()])
    password = PasswordField('Password', [DataRequired()])


class RegisterForm(Form):
    email = StringField(
        'Email Address',
        validators=[DataRequired(), Email(message=None), Length(min=6, max=40)])
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=6, max=25)]
    )
    confirm = PasswordField(
        'Confirm password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )

class UploadForm(Form):
    file = FileField('', validators=[DataRequired()])

class ConnectForm(Form):
    host = StringField('Host', [DataRequired()])
    user = StringField('User')
    password = PasswordField('Password')
    database = StringField('Database', [DataRequired()])
    table = StringField('Table', [DataRequired()])