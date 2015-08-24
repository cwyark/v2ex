#!/usr/bin/env python
# coding=utf-8

import os
import random
import re

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from v2ex.babel.ext.cookies import Cookies
from v2ex.babel import SYSTEM_VERSION
from v2ex.babel.ua import detect
from v2ex.babel.da import GetSite
from v2ex.babel.locale import GetMessages
from v2ex.babel.security import CheckAuth

class BaseHandler(webapp.RequestHandler):

    def __init__(self, request, response):
        self.initialize(request, response)

    @property
    def template_values(self):
        if not hasattr(self, "_values"):
            self._values = {}
            self._values['rnd'] = random.randrange(1, 100)
            self._values['site'] = self.site
            self._values['member'] = self.member
            self._values['blocked'] = self.blocked
            self._values['l10n'] = self.l10n
            self._values['user_agent'] = self.user_agent
            self._values['page_title'] = self.site.title.decode('utf-8') + u' › '
            self._values['canonical'] = 'http://' + str(self.site.domain) + '/'
            self._values['system_version'] = SYSTEM_VERSION
        return self._values

    @property
    def user_agent(self):
        if not hasattr(self, "_browser"):
            self._browser = detect(self.request)
        return self._browser   

    @property
    def site(self):
        if not hasattr(self, "_site"):
            self._site = GetSite()
        return self._site
    
    @property
    def member(self):
        if not hasattr(self, "_member"):
            self._member = CheckAuth(self)
        return self._member

    @property
    def blocked(self):
        if not hasattr(self, "_blocked"):
            if self.member:
                try:
                    self._blocked = ','.join(map(str, pickle.loads(self.member.blocked.encode('utf-8'))))
                except:
                    self._blocked = []
            else:
                self._blocked=[]
        return self._blocked

    @property
    def l10n(self):
        if not hasattr(self, "_l10n"):
            self._l10n = GetMessages(self.member, self.site)
        return self._l10n

    @property
    def page_title(self):
        return self.site.title
    
    def finalize(self, template_name, mobile_optimized=False, template_root='desktop', template_type='html'):
        """Insert common values into handler's dictionary for template.
        
        Load proper template according to current browser capacity.
        
        Mobile optimized templates are optional. Default to False.
        """
        output = self.render(template_name=template_name, template_root=template_root,template_type=template_type)
        self.response.out.write(output)
    
    def render(self, template_name, template_root='desktop', template_type='html'):
        path = os.path.join('tpl', template_root, template_name + '.' + template_type)
        return template.render(path, self.template_values)


    def escape(self, text):
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    @property
    def is_member(self):
        """
        return
            True:   this member is verified
            False:  this member is not verified or none
        """
        if self.member is not None:
            return True
        else:
            return False
