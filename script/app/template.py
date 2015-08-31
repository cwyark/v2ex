#!/usr/bin/env python
# coding=utf-8

import os
import re
import time
import datetime
import hashlib
import string
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
from v2ex.babel import Note

from v2ex.babel import SYSTEM_VERSION

from v2ex.babel.security import *
from v2ex.babel.ua import *
from v2ex.babel.da import *
from v2ex.babel.locale import *
from v2ex.babel.ext.cookies import Cookies
from v2ex.babel.handlers import BaseHandler
template.register_template_library('v2ex.templatetags.filters')

class MyNodesHandler(BaseHandler):
    def get(self):
        if self.is_member:
            self.template_values['page_title'] = self.site.title + u' › 我收藏的节点'
            self.finalize(template_name='my_nodes')
        else:
            self.redirect('/')
