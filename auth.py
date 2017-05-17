#!/usr/bin/env python
# coding=utf-8

import os
import re
import time
import datetime
import hashlib
import string
import random
import logging

from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from v2ex.babel import Member
from v2ex.babel import Counter
from v2ex.babel import Section
from v2ex.babel import Node
from v2ex.babel import Topic
from v2ex.babel import Reply
from v2ex.babel import Note

from v2ex.babel import SYSTEM_VERSION

from v2ex.babel.security import *
from v2ex.babel.ua import *
from v2ex.babel.da import *
from v2ex.babel.l10n import *
from v2ex.babel.ext.cookies import Cookies
from v2ex.babel.ext.sessions import Session

from v2ex.babel.handlers import BaseHandler

from simpleauth import SimpleAuthHandler

import config

FACEBOOK_AVATAR_URL = 'https://graph.facebook.com/{0}/picture?type=large'
DEFAULT_AVATAR_URL = '/img/missing-avatar.png'


class AuthHandler(BaseHandler, SimpleAuthHandler):
    """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

    # Enable optional OAuth 2.0 CSRF guard
    OAUTH2_CSRF_STATE = True
    
    USER_ATTRS = {
        'facebook': {
          'id': lambda id: ('avatar_url', FACEBOOK_AVATAR_URL.format(id)),
          'name': 'name',
          'link': 'link'
        },
        'googleplus': {
          'image': lambda img: ('avatar_url', img.get('url', DEFAULT_AVATAR_URL)),
          'displayName': 'name',
          'url': 'link',
          'emails': "emails"
        },
        'twitter': {
          'profile_image_url': 'avatar_url',
          'screen_name': 'name',
          'link': 'link'
        },
        'linkedin2': {
          'picture-url': 'avatar_url',
          'first-name': 'name',
          'public-profile-url': 'link'
        }
    }

    session = Session()

    def _on_signin(self, data, auth_info, provider, extra=None):
        """Callback whenever a new or existing user is logging in.
         data is a user info dictionary.
         auth_info contains access token or oauth token and secret.
         extra is a dict with additional params passed to the auth init handler.
        """
        logging.debug('Got user data: %s', data)

        auth_id = '%s:%s' % (provider, data['id'])

        logging.debug('Looking for a user with id %s', auth_id)
        _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

        logging.debug(_attrs)

        if self.member:
            logging.debug('Found existing user to log in')
            # Existing users might've changed their profile data so we update our
            # local model anyway. This might result in quite inefficient usage
            # of the Datastore, but we do this anyway for demo purposes.
            #
            # In a real app you could compare _attrs with user's properties fetched
            # from the datastore and update local user in case something's changed.
            #user.populate(**_attrs)
            #user.put()
            #self.auth.set_session(self.auth.store.user_to_dict(user))

        else:
            # if not a authed member
            member = Member()
            q = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'member.max')
            if (q.count() == 1):
                counter = q[0]
                counter.value = counter.value + 1
            else:
                counter = Counter()
                counter.name = 'member.max'
                counter.value = 1
            q2 = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'member.total')
            if (q2.count() == 1):
                counter2 = q2[0]
                counter2.value = counter2.value + 1
            else:
                counter2 = Counter()
                counter2.name = 'member.total'
                counter2.value = 1

            member.num = counter.value
            member.username = _attrs.get("name", "Unknown")
            member.username_lower = member.username.lower()
            member.password = None
            #member.email = member_email.lower()
            emails = _attrs.get("emails", list)
            email = emails[0].get("value", None)
            member.email = email
            #member.auth = hashlib.sha1(str(member.num) + ':' + member.password).hexdigest()
            member.auth = auth_id
            member.l10n = self.site.l10n
            member.newbie = 1
            member.noob = 0
            if member.num == 1:
                member.level = 0
            else:
                member.level = 1000
            member.put()
            counter.put()
            counter2.put()
            self.response.headers['Set-Cookie'] = str('auth=' + member.auth + '; expires=' + (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%a, %d-%b-%Y %H:%M:%S GMT") + '; path=/')
            memcache.delete('member_total')


            # Remember auth data during redirect, just for this demo. You wouldn't
            # normally do this.
            #self.session.add_flash(auth_info, 'auth_info')
            #self.session.add_flash({'extra': extra}, 'extra')

        self.redirect("/")

    def logout(self):
        self.redirect('/signout')

    def handle_exception(self, exception, debug):
        logging.error(exception)
        self.redirect("/")
        
    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)

    def _get_consumer_info_for(self, provider):
        """Returns a tuple (key, secret) for auth init requests."""
        return config.AUTH_CONFIG[provider]

    def _get_optional_params_for(self, provider):
        """Returns optional parameters for auth init requests."""
        return config.AUTH_OPTIONAL_PARAMS.get(provider)
          	
    def _to_user_model_attrs(self, data, attrs_map):
        """Get the needed information from the provider dataset."""
        user_attrs = {}
        for k, v in attrs_map.iteritems():
          attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
          user_attrs.setdefault(*attr)

        return user_attrs
  
routes = [
    webapp.Route('/auth/logout',
        handler='auth.AuthHandler:logout', name='logout'),
    webapp.Route('/auth/<provider>',
        handler='auth.AuthHandler:_simple_auth', name='auth_login'),
    webapp.Route('/auth/<provider>/callback',
        handler='auth.AuthHandler:_auth_callback', name='auth_callback')
]

application = webapp.WSGIApplication(routes, debug=True)

def main():
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
