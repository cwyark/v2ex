import re
import time

from google.appengine.ext import db
from wtforms import Form, StringField, FormField, validators, SubmitField, ValidationError, Field
from recaptcha.client import captcha
import hashlib


class UserPasswordForm(Form):
    username = StringField('username', [validators.Length(min=4, max=32, message="username should be less than 32 chars, more than 3 chars"), validators.Required(message="username is required")])
    password = StringField('password', [validators.Length(min=4, max=32, message="password should be less than 32 chars, more than 3 chars"), validators.Required(message="password is required")])


class SignInForm(UserPasswordForm):

    def __init__(self, *args, **kwargs):
        UserPasswordForm.__init__(self, *args, **kwargs)
        self.member = None
    
    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        p_sha1 = hashlib.sha1(self.password.data).hexdigest()
        q = db.GqlQuery("SELECT * FROM Member WHERE username_lower = :1", self.username.data.lower())
        if q.count() == 1:
            self.member = q.get()
            if self.member.password == p_sha1:
                return True
            else:
                self.password.errors.append("You password is not correct")
                self.member = None
                return False
        else:
            self.username.errors.append("Username is not exist")
            return False


class SignUpForm(UserPasswordForm):
    email = StringField('email', [validators.Email(message="this email is not in a valid format"), validators.Required(message="email is required")])

    def __init__(self, *args, **kwargs):
        UserPasswordForm.__init__(self, *args, **kwargs)
        self.member = None
    
    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        if re.search('^[a-zA-Z0-9\_]+$', self.username.data):
            q = db.GqlQuery('SELECT __key__ FROM Member WHERE username_lower = :1', self.username.data.lower())
            if q.count() > 0:
                self.username.errors.append("this username has been taken")
                return False
        else:
            self.username.errors.append("this username is not a effective format")
            return False
        
        q = db.GqlQuery('SELECT __key__ FROM Member WHERE email = :1', self.email.data)
        if q.count() > 0:
            self.email.errors.append("this email has been taken")
            return False

        return True

class RecaptchaFrom(Form):
    recaptcha_challenge_field = StringField('recaptcha_challenge_field', [validators.Required(message="recaptcha code is required")])
    recaptcha_response_field = StringField('recaptcha_response_field', [validators.Required(message="recaptcha code is required")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.request = kwargs['request']
        self.recaptcha_public_key = kwargs['recaptcha_public_key']
        self.recaptcha_private_key = kwargs['recaptcha_private_key']
        self.chtml = None

    def validate(self):
        cResponse = captcha.submit(
            self.recaptcha_challenge_field.data,
            self.recaptcha_response_field.data,
            self.recaptcha_private_key,
            self.request.remote_addr)
        
        self.chtml = captcha.displayhtml(
            public_key = self.recaptcha_public_key,
            use_ssl = False,
            error = cResponse.error_code)

        rv = Form.validate(self)
        if not rv:
            return False
        if cResponse.is_valid:
            return True
        else:
            self.recaptcha_response_field.errors.append("incorrect recaptcha code")
            return False


class ForgotForm(Form):
    username = StringField('username', [validators.Length(min=4, max=32, message="username should be less than 32 chars, more than 3 chars"), validators.Required(message="username is required")])
    email = StringField('email', [validators.Email(message="this email is not in a valid format"), validators.Required(message="email is required")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.member  = None
    
    def validate(self):
        
        q = db.GqlQuery('SELECT * FROM Member WHERE username_lower = :1 AND email = :2', self.username.data.lower(), self.email.data)

        rv = Form.validate(self)
        if not rv:
            return False

        if q.count() == 1:
            self.member = q.get()
            return True
        else:
            self.username.errors.append('username or email is not exist')
            return False


class PasswordResetForm(Form):
    email = StringField('email', [validators.Email(message="this email is not in a valid format"), validators.Required(message="email is required")])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
    
    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        q = db.GqlQuery("SELECT * FROM PasswordResetToken WHERE timestamp > :1 AND email = :2", (int(time.time()) - 86400), self.email.data)

        if q.count() > 0:
            self.email.errors.append('You cannot reset your password twice in 24 hors')
            return False
        else:
            return True



