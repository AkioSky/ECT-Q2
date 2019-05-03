from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp

from models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 254), Email()],
                           render_kw={"placeholder": "Username"})
    password = PasswordField('Password', validators=[DataRequired()],
                             render_kw={"placeholder": "Password"})


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)], render_kw={"placeholder": "Name"})
    username = StringField('Username', validators=[DataRequired(), Length(1, 254), Email()],
                           render_kw={"placeholder": "Username"})
    password = PasswordField('Password',
                             validators=[DataRequired(), Length(8, 16),
                                         EqualTo('confirm_password', 'Password must be equal to Confirm Password.')],
                             render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('Confirm password', validators=[DataRequired()],
                                     render_kw={"placeholder": "Confirm Password"})

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('The username is already in use.')


class UploadVideo(FlaskForm):
    upload = FileField('Upload', validators=[
        FileRequired(),
        FileAllowed(['mp4', 'wmv'], 'The file format should be .mp4 or .wmv')
    ])
    description = TextAreaField('Description', validators=[DataRequired(), Length(1, 512)])


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    avatar = FileField('Avatar', validators=[FileAllowed(['jpg', 'png'], 'Images only')])
