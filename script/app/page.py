#!/usr/bin/env python
# coding=utf-8

import os
import datetime
import random

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
from v2ex.babel import Site

from v2ex.babel.security import *
from v2ex.babel.ua import *
from v2ex.babel.da import *
from v2ex.babel.locale import *
from v2ex.babel.ext.cookies import Cookies
from v2ex.babel.handlers import BaseHandler
template.register_template_library('v2ex.templatetags.filters')

class AboutHandler(BaseHandler):
    def get(self):
        note = GetKindByNum('Note', 127)
        if note is False:
            note = GetKindByNum('Note', 2)
        self.template_values['note'] = note
        self.template_values['page_title'] = self.site.title + u' › About'
        self.finalize(template_name='about')
        
class FAQHandler(BaseHandler):
    def get(self):
        note = GetKindByNum('Note', 195)
        if note is False:
            note = GetKindByNum('Note', 4)
        self.template_values['note'] = note
        self.template_values['page_title'] = self.site.title + u' › FAQ'
        self.finalize(template_name='faq')

class MissionHandler(BaseHandler):
    def get(self):
        note = GetKindByNum('Note', 240)
        if note is False:
            note = GetKindByNum('Note', 5)
        self.template_values['note'] = note
        self.template_values['page_title'] = self.site.title + u' › Mission'
        self.finalize(template_name='mission')

class AdvertiseHandler(BaseHandler):
    def get(self):
        self.template_values['page_title'] = self.site.title + u' › Advertise'
        self.finalize(template_name='advertise')

class AdvertisersHandler(BaseHandler):
    def get(self):
        self.template_values['page_title'] = self.site.title + u' › Advertisers'
        self.finalize(template_name='advertisers')
