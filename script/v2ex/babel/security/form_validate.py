import re

from google.appengine.ext import db
from wtforms import Form, StringField, FormField, validators, SubmitField, ValidationError, Field
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
