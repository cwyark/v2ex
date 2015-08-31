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
from v2ex.babel.ext.sessions import Session

from v2ex.babel.handlers import BaseHandler

template.register_template_library('v2ex.templatetags.filters')

class MyNodesHandler(BaseHandler):
    def get(self):
        if self.is_member:
            self.template_values['page_title'] = self.site.title + u' › 我收藏的节点'
            if self.member.favorited_nodes > 0:
                self.template_values['has_nodes'] = True
                q = db.GqlQuery("SELECT * FROM NodeBookmark WHERE member = :1 ORDER BY created DESC LIMIT 0,15", self.member)
                self.template_values['column_1'] = q
                if self.member.favorited_nodes > 15:
                    q2 = db.GqlQuery("SELECT * FROM NodeBookmark WHERE member = :1 ORDER BY created DESC LIMIT 15,15", self.member)
                    self.template_values['column_2'] = q2
            else:
                self.template_values['has_nodes'] = False
            self.finalize(template_name='my_nodes')
        else:
            self.redirect('/')

class MyTopicsHandler(BaseHandler):
    def get(self):
        if self.is_member:
            self.template_values['page_title'] = self.site.title + u' › 我收藏的主题'
            if self.member.favorited_topics > 0:
                self.template_values['has_topics'] = True
                q = db.GqlQuery("SELECT * FROM TopicBookmark WHERE member = :1 ORDER BY created DESC", self.member)
                bookmarks = []
                for bookmark in q:
                    try:
                        topic = bookmark.topic
                        bookmarks.append(bookmark)
                    except:
                        bookmark.delete()
                self.template_values['bookmarks'] = bookmarks
            else:
                self.template_values['has_topics'] = False
            self.finalize(template_name='my_topics')
        else:
            self.redirect('/')
            
class MyFollowingHandler(BaseHandler):
    def get(self):
        if self.is_member:
            self.template_values['page_title'] = self.site.title + u' › 我的特别关注'
            if self.member.favorited_members > 0:
                self.template_values['has_following'] = True
                q = db.GqlQuery("SELECT * FROM MemberBookmark WHERE member_num = :1 ORDER BY created DESC", self.member.num)
                self.template_values['following'] = q
                following = []
                for bookmark in q:
                    following.append(bookmark.one.num)
                q2 = db.GqlQuery("SELECT * FROM Topic WHERE member_num IN :1 ORDER BY created DESC LIMIT 20", following)
                self.template_values['latest'] = q2
            else:
                self.template_values['has_following'] = False
            self.finalize(template_name='my_following')
        else:
            self.redirect('/')
