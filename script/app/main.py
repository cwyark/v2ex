#!/usr/bin/env python
# coding=utf-8

import base64
import os
import re
import time
import datetime
import hashlib
import urllib
import random
import pickle
import math

from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from v2ex.babel import Member
from v2ex.babel import Counter
from v2ex.babel import Section
from v2ex.babel import Node
from v2ex.babel import Topic
from v2ex.babel import Reply
from v2ex.babel import PasswordResetToken

from v2ex.babel import SYSTEM_VERSION

from v2ex.babel.security import *
from v2ex.babel.security.form_validate import *
from v2ex.babel.ua import *
from v2ex.babel.da import *
from v2ex.babel.locale import *
from v2ex.babel.ext.cookies import Cookies
from v2ex.babel.ext.sessions import Session

from v2ex.babel.handlers import BaseHandler

from django.utils import simplejson as json

from recaptcha.client import captcha

template.register_template_library('v2ex.templatetags.filters')

import config


class HomeHandler(BaseHandler):
    def get(self):
        if self.is_member:
            if self.member.my_home is not None and len(self.member.my_home) > 0:
                return self.redirect(self.member.my_home)

            member_recent_nodes = GetMemberRecentNodes(self.member.num)
            if member_recent_nodes:
                self.template_values['member_recent_nodes'] = member_recent_nodes

# cache latest topic to save db access resource
        site_landingpagecache = GetSiteLandingPageCache()
        if site_landingpagecache is None:
            self.template_values['site_latest_topics'] = GetLatestTopic(16)
            site_landingpagecache = self.render(template_name='landingpage', template_root='cache', template_type='html')
            SetSiteLandingPageCache(site_landingpagecache)

        self.template_values['site_landingpagecache'] = site_landingpagecache
        self.template_values['site_new_nodes'] = GetSiteRecentNewNodes()
        self.template_values['site_total_member_number'] = GetTotalMemberNum()
        self.template_values['site_total_topic_number'] = GetTotalTopicNum()
        self.template_values['site_total_reply_number'] = GetTotalReplyNum()
        self.template_values['site_hottest_nodes'] = GetSiteHottestNode()
        self.template_values['site_index_category'] = GetIndexCategory(self.site)
        self.finalize(template_name='index')


class PlanesHandler(BaseHandler):
    def get(self):
        (planes_counter, planes) = GetAllSectionAndNodes()
        self.template_values['planes_counter'] = planes_counter
        self.template_values['planes'] = planes
        self.finalize(template_name='planes')


class RecentHandler(BaseHandler):
    def get(self):
        latest = GetLatestTopic(number=50)
        self.template_values['latest'] = latest
        self.template_values['latest_total'] = len(latest)
        expires_date = datetime.datetime.utcnow() + datetime.timedelta(minutes=2)
        expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
        self.response.headers.add_header("Expires", expires_str)
        self.response.headers['Cache-Control'] = 'max-age=120, must-revalidate'
        self.finalize(template_name='recent')


class SigninHandler(BaseHandler):
    def get(self):
        if self.member is not None:
            self.redirect("/")
        errors = 0
        self.template_values['errors'] = errors
        self.template_values['next'] = self.request.referer
        self.finalize(template_name='signin')

    def post(self):

        if self.member is not None:
            self.abort(404)

        u = self.request.get('username').strip()
        p = self.request.get('password').strip()

        form = SignInForm(self.request.POST)
        if form.validate() is True:
            self.response.headers['Set-Cookie'] = str('auth=' + form.member.auth + '; expires=' + (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%a, %d-%b-%Y %H:%M:%S GMT") + '; path=/')
            next = self.request.get('next').strip()
            host = self.request.host + '/'
            if next.rfind(host)>0 and not next.rfind('/sign'):
                self.redirect(next)
            else:
                self.redirect('/')

        self.template_values['u'] = u
        self.template_values['p'] = p
        self.template_values['error_message'] = form.errors
        self.finalize(template_name='signin')


class SignupHandler(BaseHandler):

    def get(self):
        if self.member is not None:
            self.redirect("/")

        chtml = captcha.displayhtml(
            public_key=config.recaptcha_public_key,
            use_ssl=False,
            error=None)
        self.template_values['errors'] = 0
        self.template_values['captchahtml'] = chtml
        self.finalize(template_name='signup')

    def post(self):
        if self.member is not None:
            self.abort(404)
        
        member_username = self.request.get('username').strip()
        member_password = self.request.get('password').strip()
        member_email = self.request.get('email').strip()
     
        form = SignUpForm(self.request.POST)
        form_result = form.validate()

        form_recaptcha = RecaptchaFrom(self.request.POST, request = self.request, recaptcha_public_key=config.recaptcha_public_key, recaptcha_private_key=config.recaptcha_private_key)
        form_recaptcha_result = form_recaptcha.validate()

        if form_result and form_recaptcha_result:

            counter_max = AddMemberNumberMax()
            counter_total = AddMemberNumberTotal()
            member = UpdateMember(number = counter_max.value, username = form.username.data, password = form.password.data, email = form.email.data, l10n = self.site.l10n)

            self.response.headers['Set-Cookie'] = str('auth=' + member.auth + '; expires=' + (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%a, %d-%b-%Y %H:%M:%S GMT") + '; path=/')

            self.redirect('/')
        else:
            self.template_values['error_message'] = form.errors
            self.template_values['recaptcha_error_message'] = form_recaptcha.errors
            self.template_values['member_username'] = member_username
            self.template_values['member_password'] = member_password
            self.template_values['member_email'] = member_email
            self.template_values['captchahtml'] = form_recaptcha.chtml
            self.finalize(template_name='signup')


class SignoutHandler(BaseHandler):
    def get(self):
        if not self.is_member:
            self.redirect("/")
        cookies = Cookies(self, max_age = 86400, path = '/')
        del cookies['auth']
        self.finalize(template_name='signout')


class ForgotHandler(BaseHandler):
    def get(self):
        self.finalize(template_name='forgot')

    def post(self):
        form = ForgotForm(self.request.POST)
        if form.validate():
            form_passwordreset = PasswordResetForm(self.request.POST)
            if form_passwordreset.validate():
                one = form.member
                token = ''.join([str(random.randint(0, 9)) for i in range(32)])
                AddPasswordResetToken(member=one, token=token)
                self.template_values['site'] = self.site
                self.template_values['one'] = one
                self.template_values['host'] = self.request.headers['Host']
                self.template_values['token'] = token
                self.template_values['ua'] = self.request.headers['User-Agent']
                self.template_values['ip'] = self.request.remote_addr
                output = self.render(template_name='reset_password', template_root='mail', template_type='txt')
                result = mail.send_mail(sender="cwyark@gmail.com",
                              to=one.email,
                              subject="=?UTF-8?B?" + base64.b64encode((u"[" + self.site.title + u"] 重新设置密码").encode('utf-8')) + "?=",
                              body=output)
                self.template_values['forgot_sent'] = 1
                self.finalize(template_name='forgot')
            else:
                self.template_values['error_message'] = form_passwordreset.errors
                self.finalize(template_name='forgot')
        else:
            self.template_values['error_message'] = form.errors
            self.finalize(template_name='forgot')


class PasswordResetHandler(BaseHandler):
    def get(self, token):
        if self.is_member:
            self.abort(404)

        token = str(token.strip().lower())
        prt = CheckTokenExist(token)
        if prt is not None:
            self.template_values['token'] = prt
            self.template_values['reset_password'] = 1
            self.finalize(template_name='reset')
        else:
            self.template_values['token_not_found'] = 1
            self.finalize(template_name='reset')
    
    def post(self, token):
        if self.is_member:
            self.abort(404)

        token = str(token.strip().lower())
        q = db.GqlQuery("SELECT * FROM PasswordResetToken WHERE token = :1 AND valid = 1", token)
        if q.count() == 1:
            prt = q[0]
            self.template_values['token'] = prt
            # Verification
            errors = 0
            new_password = str(self.request.get('new_password').strip())
            new_password_again = str(self.request.get('new_password_again').strip())
            if new_password is '' or new_password_again is '':
                errors = errors + 1
                error_message = '請輸入兩次新密碼'
            if errors == 0:
                if new_password != new_password_again:
                    errors = errors + 1
                    error_message = '兩次輸入的新密碼不一致'
            if errors == 0:
                if len(new_password) > 32:
                    errors = errors + 1
                    error_message = '新密碼長度不能超過32個字母'
            if errors == 0:
                q2 = db.GqlQuery("SELECT * FROM Member WHERE num = :1", prt.member.num)
                one = q2[0]
                one.password = hashlib.sha1(new_password).hexdigest()
                one.auth = hashlib.sha1(str(one.num) + ':' + one.password).hexdigest()
                one.put()
                prt.valid = 0
                prt.put()
                self.template_values['reset_password_ok'] = 1
                self.finalize(template_name='reset_password_ok')
            else:
                self.template_values['errors'] = errors
                self.template_values['error_message'] = error_message
                self.template_values['reset_password'] = 1
                self.finalize(template_name='reset')
        else:
            self.template_values['token_not_found'] = 1
            self.finalize(template_name='reset')


class NodeGraphHandler(BaseHandler):
    def get(self, node_name):
        self.session = Session()
        can_create = False
        can_manage = False
        if self.site.topic_create_level > 999:
            if self.member:
                can_create = True
        else:
            if self.member:
                if self.member.level <= site.topic_create_level:
                    can_create = True
        if self.member:
            if self.member.level == 0:
                can_manage = True
        self.template_values['can_create'] = can_create
        self.template_values['can_manage'] = can_manage
        node = GetKindByName('Node', node_name)
        self.template_values['node'] = node
        if node:
            self.template_values['feed_link'] = '/feed/' + node.name + '.xml'
            self.template_values['feed_title'] = self.site.title + u' › ' + node.title
            self.template_values['canonical'] = 'http://' + str(self.site.domain) + '/go/' + node.name
            if node.parent_node_name is None:
                siblings = []
            else:
                siblings = db.GqlQuery("SELECT * FROM Node WHERE parent_node_name = :1 AND name != :2", node.parent_node_name, node.name)
            self.template_values['siblings'] = siblings
            if self.member:
                favorited = self.member.hasFavorited(node)
                self.template_values['favorited'] = favorited
                recent_nodes = memcache.get('member::' + str(self.member.num) + '::recent_nodes')
                recent_nodes_ids = memcache.get('member::' + str(self.member.num) + '::recent_nodes_ids')
                if recent_nodes and recent_nodes_ids:
                    if (node.num in recent_nodes_ids) is not True:
                        recent_nodes.insert(0, node)
                        recent_nodes_ids.insert(0, node.num)
                        memcache.set('member::' + str(self.member.num) + '::recent_nodes', recent_nodes, 7200)
                        memcache.set('member::' + str(self.member.num) + '::recent_nodes_ids', recent_nodes_ids, 7200)
                else:
                    recent_nodes = []
                    recent_nodes.append(node)
                    recent_nodes_ids = []
                    recent_nodes_ids.append(node.num)
                    memcache.set('member::' + str(self.member.num) + '::recent_nodes', recent_nodes, 7200)
                    memcache.set('member::' + str(self.member.num) + '::recent_nodes_ids', recent_nodes_ids, 7200)
                self.template_values['recent_nodes'] = recent_nodes
            self.template_values['page_title'] = self.site.title + u' › ' + node.title
        else:
            self.template_values['page_title'] = self.site.title + u' › 節點未找到'
        section = False
        if node:
            section = GetKindByNum('Section', node.section_num)
        self.template_values['section'] = section

        if (node):
            self.finalize(template_name='node_graph')
        else:
            self.finalize(template_name='node_not_found')

class NodeHandler(BaseHandler):
    def get(self, node_name):
        self.session = Session()
        can_create = False
        can_manage = False
        if self.site.topic_create_level > 999:
            if self.member:
                can_create = True
        else:
            if self.member:
                if self.member.level <= self.site.topic_create_level:
                    can_create = True
        if self.member:
            if self.member.level == 0:
                can_manage = True
        self.template_values['can_create'] = can_create
        self.template_values['can_manage'] = can_manage
        self.template_values['site_hottest_nodes'] = GetSiteHottestNode()
        node = GetKindByName('Node', node_name)
        self.template_values['node'] = node
        pagination = False
        pages = 1
        page = 1
        page_size = 15
        start = 0
        has_more = False
        more = 1
        has_previous = False
        previous = 1
        if node:
            self.template_values['feed_link'] = '/feed/' + node.name + '.xml'
            self.template_values['feed_title'] = self.site.title + u' › ' + node.title
            self.template_values['canonical'] = 'http://' + str(self.site.domain) + '/go/' + node.name
            if self.member:
                favorited = self.member.hasFavorited(node)
                self.template_values['favorited'] = favorited
                recent_nodes = memcache.get('member::' + str(self.member.num) + '::recent_nodes')
                recent_nodes_ids = memcache.get('member::' + str(self.member.num) + '::recent_nodes_ids')
                if recent_nodes and recent_nodes_ids:
                    if (node.num in recent_nodes_ids) is not True:
                        recent_nodes.insert(0, node)
                        recent_nodes_ids.insert(0, node.num)
                        memcache.set('member::' + str(self.member.num) + '::recent_nodes', recent_nodes, 7200)
                        memcache.set('member::' + str(self.member.num) + '::recent_nodes_ids', recent_nodes_ids, 7200)
                else:
                    recent_nodes = []
                    recent_nodes.append(node)
                    recent_nodes_ids = []
                    recent_nodes_ids.append(node.num)
                    memcache.set('member::' + str(self.member.num) + '::recent_nodes', recent_nodes, 7200)
                    memcache.set('member::' + str(self.member.num) + '::recent_nodes_ids', recent_nodes_ids, 7200)
                self.template_values['recent_nodes'] = recent_nodes
            self.template_values['page_title'] = self.site.title + u' › ' + node.title
            # Pagination
            if node.topics > page_size:
                pagination = True
            else:
                pagination = False
            if pagination:
                if node.topics % page_size == 0:
                    pages = int(node.topics / page_size)
                else:
                    pages = int(node.topics / page_size) + 1
                page = self.request.get('p')
                if (page == '') or (page is None):
                    page = 1
                else:
                    page = int(page)
                    if page > pages:
                        page = pages
                    else:
                        if page < 1:
                            page = 1
                if page < pages:
                    has_more = True
                    more = page + 1
                if page > 1:
                    has_previous = True
                    previous = page - 1    
                start = (page - 1) * page_size
                self.template_values['canonical'] = 'http://' + str(self.site.domain) + '/go/' + node.name + '?p=' + str(page)
        else:
            self.template_values['page_title'] = self.site.title + u' › 节点未找到'
        self.template_values['pagination'] = pagination
        self.template_values['pages'] = pages
        self.template_values['page'] = page
        self.template_values['page_size'] = page_size
        self.template_values['has_more'] = has_more
        self.template_values['more'] = more
        self.template_values['has_previous'] = has_previous
        self.template_values['previous'] = previous
        section = False
        if node:
            section = GetKindByNum('Section', node.section_num)
        self.template_values['section'] = section
        topics = False
        if node:
            q3 = db.GqlQuery("SELECT * FROM Topic WHERE node_num = :1 ORDER BY last_touched DESC LIMIT " + str(start) + ", " + str(page_size), node.num)
            topics = q3
        self.template_values['latest'] = topics
        
        if (node):
            self.finalize(template_name='node')
        else:
            self.finalize(template_name='node_not_found')

class NodeApiHandler(BaseHandler):
    def get(self, node_name):
        node = GetKindByName('Node', node_name)
        if node:
            self.template_values['node'] = node
            self.response.headers['Content-type'] = 'application/json;charset=UTF-8'
            self.finalize(template_name='node', template_root='api', template_type='json')
        else:
            self.error(404)

class SearchHandler(webapp.RequestHandler):
    def get(self, q):
        q = urllib.unquote(q)
        self.template_values['page_title'] = self.site.title + u' › 搜索 ' + q.decode('utf-8')
        self.template_values['q'] = q
        if config.fts_enabled is not True:
            self.finalize(template_name='search_unavailable')
        else:
            if re.findall('^([a-zA-Z0-9\_]+)$', q):
                node = GetKindByName('Node', q.lower())
                if node is not None:
                    self.template_values['node'] = node
            # Fetch result
            q_lowered = q.lower()
            q_md5 = hashlib.md5(q_lowered).hexdigest()
            topics = memcache.get('q::' + q_md5)
            if topics is None:
                try:
                    if os.environ['SERVER_SOFTWARE'] == 'Development/1.0':
                        fts = u'http://127.0.0.1:20000/search?q=' + str(urllib.quote(q_lowered))
                    else:
                        fts = u'http://' + config.fts_server + '/search?q=' + str(urllib.quote(q_lowered))
                    response = urlfetch.fetch(fts, headers = {"Authorization" : "Basic %s" % base64.b64encode(config.fts_username + ':' + config.fts_password)})
                    if response.status_code == 200:
                        results = json.loads(response.content)
                        topics = []
                        for num in results:
                            topics.append(GetKindByNum('Topic', num))
                        self.template_values['topics'] = topics
                        memcache.set('q::' + q_md5, topics, 86400)
                except:
                    self.template_values['topics'] = []
            else:
                self.template_values['topics'] = topics
            self.finalize(template_name='search')


class DispatcherHandler(webapp.RequestHandler):
    def post(self):
        referer = self.request.headers['Referer']
        q = self.request.get('q').strip()
        if len(q) > 0:
            self.redirect('/q/' + q)
        else:
            self.redirect(referer)

class RouterHandler(webapp.RequestHandler):
    def get(self, path):
        if path.find('/') != -1:
            # Page
            parts = path.split('/')
            if len(parts) == 2:
                minisite_name = parts[0]
                if parts[1] == '':
                    page_name = 'index.html'
                else:
                    page_name = parts[1]
                minisite = GetKindByName('Minisite', minisite_name)
                if minisite is not False:
                    page = memcache.get(path)
                    if page is None:
                        q = db.GqlQuery("SELECT * FROM Page WHERE name = :1 AND minisite = :2", page_name, minisite)
                        if q.count() == 1:
                            page = q[0]
                            memcache.set(path, page, 864000)
                    if page.mode == 1:
                        # Dynamic embedded page
                        template_values = {}
                        site = GetSite()
                        template_values['site'] = site
                        member = CheckAuth(self)
                        if member:
                            template_values['member'] = member
                        l10n = GetMessages(self, member, site)
                        template_values['l10n'] = l10n
                        template_values['rnd'] = random.randrange(1, 100)
                        template_values['page'] = page
                        template_values['minisite'] = page.minisite
                        template_values['page_title'] = site.title + u' › ' + page.minisite.title.decode('utf-8') + u' › ' + page.title.decode('utf-8')
                        taskqueue.add(url='/hit/page/' + str(page.key()))
                        path = os.path.join(os.path.dirname(__file__), 'tpl', 'desktop', 'page.html')
                        output = template.render(path, template_values)
                        self.response.out.write(output)
                    else:
                        # Static standalone page
                        taskqueue.add(url='/hit/page/' + str(page.key()))
                        expires_date = datetime.datetime.utcnow() + datetime.timedelta(days=10)
                        expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
                        self.response.headers.add_header("Expires", expires_str)
                        self.response.headers['Cache-Control'] = 'max-age=864000, must-revalidate'
                        self.response.headers['Content-Type'] = page.content_type
                        self.response.out.write(page.content)
            else:
                minisite_name = parts[0]
                page_name = 'index.html'
                minisite = GetKindByName('Minisite', minisite_name)
                if minisite is not False:
                    page = memcache.get(path)
                    if page is None:
                        q = db.GqlQuery("SELECT * FROM Page WHERE name = :1 AND minisite = :2", page_name, minisite)
                        if q.count() == 1:
                            page = q[0]
                            memcache.set(path, page, 864000)
                    if page.mode == 1:
                        # Dynamic embedded page
                        template_values = {}
                        site = GetSite()
                        template_values['site'] = site
                        member = CheckAuth(self)
                        if member:
                            template_values['member'] = member
                        l10n = GetMessages(self, member, site)
                        template_values['l10n'] = l10n
                        template_values['rnd'] = random.randrange(1, 100)
                        template_values['page'] = page
                        template_values['minisite'] = page.minisite
                        template_values['page_title'] = site.title + u' › ' + page.minisite.title.decode('utf-8') + u' › ' + page.title.decode('utf-8')
                        taskqueue.add(url='/hit/page/' + str(page.key()))
                        path = os.path.join(os.path.dirname(__file__), 'tpl', 'desktop', 'page.html')
                        output = template.render(path, template_values)
                        self.response.out.write(output)
                    else:
                        # Static standalone page
                        taskqueue.add(url='/hit/page/' + str(page.key()))
                        expires_date = datetime.datetime.utcnow() + datetime.timedelta(days=10)
                        expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
                        self.response.headers.add_header("Expires", expires_str)
                        self.response.headers['Cache-Control'] = 'max-age=864000, must-revalidate'
                        self.response.headers['Content-Type'] = page.content_type
                        self.response.out.write(page.content)
        else:
            # Site
            page = memcache.get(path + '/index.html')
            if page:
                taskqueue.add(url='/hit/page/' + str(page.key()))
                if page.mode == 1:
                    # Dynamic embedded page
                    template_values = {}
                    site = GetSite()
                    template_values['site'] = site
                    member = CheckAuth(self)
                    if member:
                        template_values['member'] = member
                    l10n = GetMessages(self, member, site)
                    template_values['l10n'] = l10n
                    template_values['rnd'] = random.randrange(1, 100)
                    template_values['page'] = page
                    template_values['minisite'] = page.minisite
                    template_values['page_title'] = site.title + u' › ' + page.minisite.title.decode('utf-8') + u' › ' + page.title.decode('utf-8')
                    taskqueue.add(url='/hit/page/' + str(page.key()))
                    path = os.path.join(os.path.dirname(__file__), 'tpl', 'desktop', 'page.html')
                    output = template.render(path, template_values)
                    self.response.out.write(output)
                else:
                    expires_date = datetime.datetime.utcnow() + datetime.timedelta(days=10)
                    expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
                    self.response.headers.add_header("Expires", expires_str)
                    self.response.headers['Cache-Control'] = 'max-age=864000, must-revalidate'
                    self.response.headers['Content-Type'] = page.content_type
                    self.response.out.write(page.content)
            else:
                minisite_name = path
                minisite = GetKindByName('Minisite', minisite_name)
                q = db.GqlQuery("SELECT * FROM Page WHERE name = :1 AND minisite = :2", 'index.html', minisite)
                if q.count() == 1:
                    page = q[0]
                    memcache.set(path + '/index.html', page, 864000)
                    if page.mode == 1:
                        # Dynamic embedded page
                        template_values = {}
                        site = GetSite()
                        template_values['site'] = site
                        member = CheckAuth(self)
                        if member:
                            template_values['member'] = member
                        l10n = GetMessages(self, member, site)
                        template_values['l10n'] = l10n
                        template_values['rnd'] = random.randrange(1, 100)
                        template_values['page'] = page
                        template_values['minisite'] = page.minisite
                        template_values['page_title'] = site.title + u' › ' + page.minisite.title.decode('utf-8') + u' › ' + page.title.decode('utf-8')
                        taskqueue.add(url='/hit/page/' + str(page.key()))
                        path = os.path.join(os.path.dirname(__file__), 'tpl', 'desktop', 'page.html')
                        output = template.render(path, template_values)
                        self.response.out.write(output)
                    else:
                        # Static standalone page
                        taskqueue.add(url='/hit/page/' + str(page.key()))
                        expires_date = datetime.datetime.utcnow() + datetime.timedelta(days=10)
                        expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
                        self.response.headers.add_header("Expires", expires_str)
                        self.response.headers['Cache-Control'] = 'max-age=864000, must-revalidate'
                        self.response.headers['Content-Type'] = page.content_type
                        self.response.out.write(page.content)

class ChangesHandler(BaseHandler):
    def get(self):
        self.template_values['page_title'] = self.site.title + u' › 全站最新更新紀錄'
        topic_total = GetTotalTopicNum()
        self.template_values['topic_total'] = topic_total
        page_size = 60
        pages = 1
        if topic_total > page_size:
            if (topic_total % page_size) > 0:
                pages = int(math.floor(topic_total / page_size)) + 1
            else:
                pages = int(math.floor(topic_total / page_size))
        try:
            page_current = int(self.request.get('p'))
            if page_current < 1:
                page_current = 1
            if page_current > pages:
                page_current = pages
        except:
            page_current = 1
        page_start = (page_current - 1) * page_size
        self.template_values['pages'] = pages
        self.template_values['page_current'] = page_current
        i = 1
        ps = []
        while i <= pages:
            ps.append(i)
            i = i + 1
        self.template_values['ps'] = ps
        
        latest = memcache.get('q_changes_' + str(page_current))
        if (latest):
            self.template_values['latest'] = latest
        else:
            q1 = db.GqlQuery("SELECT * FROM Topic ORDER BY last_touched DESC LIMIT " + str(page_start) + "," + str(page_size))
            topics = []
            for topic in q1:
                topics.append(topic)
            memcache.set('q_changes_' + str(page_current), topics, 120)
            self.template_values['latest'] = topics
            self.template_values['latest_total'] = len(topics)
        self.finalize(template_name='changes')
