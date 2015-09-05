#!/usr/bin/env python
# coding=utf-8

import os
import random
import re
import sys


import webapp2
from webapp2_extras import jinja2

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.ext import webapp

from v2ex.babel.ext.cookies import Cookies
from v2ex.babel import SYSTEM_VERSION
from v2ex.babel.ua import detect
from v2ex.babel.da import GetSite
from v2ex.babel.locale import GetMessages
from v2ex.babel.security import CheckAuth

from v2ex.babel.da import GetTotalTopicNum, GetTotalReplyNum, GetTotalMemberNum, GetSiteHottestNode, GetSiteRecentNewNodes

reload(sys)
sys.setdefaultencoding('utf-8')

class BaseHandler(webapp2.RequestHandler):
    
    def __init__(self, request, response):
        self.initialize(request, response)
    
    @webapp2.cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

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
            self.template_values['site_total_member_number'] = GetTotalMemberNum()
            self.template_values['site_total_topic_number'] = GetTotalTopicNum()
            self.template_values['site_total_reply_number'] = GetTotalReplyNum()
            self.template_values['site_new_nodes'] = GetSiteRecentNewNodes()
            self.template_values['site_hottest_nodes'] = GetSiteHottestNode()
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
        path = os.path.join(template_root, template_name + '.' + template_type)
        return self.jinja2.render_template(path, **self.template_values)

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
