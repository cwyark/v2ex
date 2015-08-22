# coding=utf-8
# "da" means Data Access, this file contains various quick (or dirty) methods for accessing data.

import hashlib
import random
import zlib
import pickle

from google.appengine.ext import db
from google.appengine.api import memcache

from v2ex.babel import Member
from v2ex.babel import Counter
from v2ex.babel import Section
from v2ex.babel import Node
from v2ex.babel import Topic
from v2ex.babel import Reply
from v2ex.babel import Place
from v2ex.babel import Site

def GetKindByNum(kind, num):
    K = str(kind.capitalize())
    one = memcache.get(K + '_' + str(num))
    if one:
        return one
    else:
        q = db.GqlQuery("SELECT * FROM " + K + " WHERE num = :1", int(num))
        if q.count() == 1:
            one = q[0]
            memcache.set(K + '_' + str(num), one, 86400)
            return one
        else:
            return False
            
def GetKindByName(kind, name):
    K = str(kind.capitalize())
    one = memcache.get(K + '::' + str(name))
    if one:
        return one
    else:
        q = db.GqlQuery("SELECT * FROM " + K + " WHERE name = :1", str(name))
        if q.count() == 1:
            one = q[0]
            memcache.set(K + '::' + str(name), one, 86400)
            return one
        else:
            return False

def GetMemberByUsername(name):
    one = memcache.get('Member::' + str(name).lower())
    if one:
        return one
    else:
        q = db.GqlQuery("SELECT * FROM Member WHERE username_lower = :1", str(name).lower())
        if q.count() == 1:
            one = q[0]
            memcache.set('Member::' + str(name).lower(), one, 86400)
            return one
        else:
            return False

def GetMemberByEmail(email):
    cache = 'Member::email::' + hashlib.md5(email.lower()).hexdigest()
    one = memcache.get(cache)
    if one:
        return one
    else:
        q = db.GqlQuery("SELECT * FROM Member WHERE email = :1", str(email).lower())
        if q.count() == 1:
            one = q[0]
            memcache.set(cache, one, 86400)
            return one
        else:
            return False

def ip2long(ip):
    ip_array = ip.split('.')
    ip_long = int(ip_array[0]) * 16777216 + int(ip_array[1]) * 65536 + int(ip_array[2]) * 256 + int(ip_array[3])
    return ip_long

def GetPlaceByIP(ip):
    cache = 'Place_' + ip
    place = memcache.get(cache)
    if place:
        return place
    else:
        q = db.GqlQuery("SELECT * FROM Place WHERE ip = :1", ip)
        if q.count() == 1:
            place = q[0]
            memcache.set(cache, place, 86400)
            return place
        else:
            return False

def CreatePlaceByIP(ip):
    place = Place()
    q = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'place.max')
    if (q.count() == 1):
        counter = q[0]
        counter.value = counter.value + 1
    else:
        counter = Counter()
        counter.name = 'place.max'
        counter.value = 1
    q2 = db.GqlQuery('SELECT * FROM Counter WHERE name = :1', 'place.total')
    if (q2.count() == 1):
        counter2 = q2[0]
        counter2.value = counter2.value + 1
    else:
        counter2 = Counter()
        counter2.name = 'place.total'
        counter2.value = 1
    place.num = ip2long(ip)
    place.ip = ip
    place.put()
    counter.put()
    counter2.put()
    return place

def GetSite():
    site = memcache.get('site')
    if site is not None:
        return site
    else:
        q = db.GqlQuery("SELECT * FROM Site WHERE num = 1")
        if q.count() == 1:
            site = q[0]
            if site.l10n is None:
                site.l10n = 'en'
            if site.meta is None:
                site.meta = ''
            memcache.set('site', site, 86400)
            return site
        else:
            site = Site()
            site.num = 1
            site.title = 'V2EX'
            site.domain = 'v2ex.appspot.com'
            site.slogan = 'way to explore'
            site.l10n = 'en'
            site.description = 'This is the test description'
            site.meta = ''
            site.put()
            memcache.set('site', site, 86400)
            return site

# input is a compressed string
# output is an object
def GetUnpacked(data):
    decompressed = zlib.decompress(data)
    return pickle.loads(decompressed)

# input is an object
# output is an compressed string
def GetPacked(data):
    s = pickle.dumps(data)
    return zlib.compress(s)

def GetSiteHottestNode():
    site_hottest_nodes = memcache.get('site_hottest_nodes')
    if site_hottest_nodes is None:
        site_hottest_nodes = []
        qhot = db.GqlQuery("SELECT * FROM Node ORDER BY topics DESC LIMIT 25")
        if qhot.count() > 0:
            for node in qhot:
                site_hottest_nodes.append(node)
        memcache.set('site_hottest_nodes', site_hottest_nodes, 86400)
    return site_hottest_nodes



def GetSiteRecentNewNodes():
    site_new_nodes = memcache.get('site_new_nodes')
    if site_new_nodes is None:
        site_new_nodes = []
        qnew = db.GqlQuery("SELECT * FROM Node ORDER BY created DESC LIMIT 10")
        if qnew.count() > 0:
            for node in qnew:
                site_new_nodes.append(node)
        memcache.set('site_new_nodes', site_new_nodes, 86400)
    return site_new_nodes


def GetTotalMemberNum():
    member_total = memcache.get('member_total')
    if member_total is None:
        q3 = db.GqlQuery("SELECT * FROM Counter WHERE name = 'member.total'")
        if (q3.count() > 0):
            member_total = q3[0].value
        else:
            member_total = 0
        memcache.set('member_total', member_total, 3600)
    return member_total


def GetTotalTopicNum():
    topic_total = memcache.get('topic_total')
    if topic_total is None:
        q4 = db.GqlQuery("SELECT * FROM Counter WHERE name = 'topic.total'")
        if (q4.count() > 0):
            topic_total = q4[0].value
        else:
            topic_total = 0
        memcache.set('topic_total', topic_total, 3600)
    return topic_total


def GetTotalReplyNum():
    reply_total = memcache.get('reply_total')
    if reply_total is None:
        q5 = db.GqlQuery("SELECT * FROM Counter WHERE name = 'reply.total'")
        if (q5.count() > 0):
            reply_total = q5[0].value
        else:
            reply_total = 0
        memcache.set('reply_total', reply_total, 3600)
    return reply_total

def GetIndexCategory(site):
    c = memcache.get('site_index_category')
    if c is None:
        c = ''
        if site.home_categories is not None:
            categories = site.home_categories.split("\n")
        else:
            categories = []
        for category in categories:
            category = category.strip()
            c = c + '<div class="cell"><table cellpadding="0" cellspacing="0" border="0"><tr><td align="right" width="60"><span class="fade">' + category + '</span></td><td style="line-height: 200%; padding-left: 10px;">'
            qx = db.GqlQuery("SELECT * FROM Node WHERE category = :1 ORDER BY topics DESC", category)
            for node in qx:
                c = c + '<a href="/go/' + node.name + '" style="font-size: 14px;">' + node.title + '</a>&nbsp; &nbsp; '
            c = c + '</td></tr></table></div>'
            memcache.set('site_index_category', c, 86400)
    return c


def GetLatestTopic(number):
    latest = memcache.get('q_latest_%d' % number)

    if not latest:
        q2 = db.GqlQuery("SELECT * FROM Topic ORDER BY last_touched DESC LIMIT %d" % number)
        topics = []
        for topic in q2:
            topics.append(topic)
        memcache.set('q_latest_%d' % number, topics, 600)
        latest = topics
    return latest

def GetAllSectionAndNodes():
    c = 0
    c = memcache.get('planes_c')
    s = ''
    s = memcache.get('planes')

    if s is None:
        c = 0
        s = ''
        q = db.GqlQuery("SELECT * FROM Section ORDER BY nodes DESC")
        if (q.count() > 0):
            for section in q:
                q2 = db.GqlQuery("SELECT * FROM Node WHERE section_num = :1 ORDER BY topics DESC", section.num)
                n = ''
                if (q2.count() > 0):
                    nodes = []
                    i = 0
                    for node in q2:
                        nodes.append(node)
                        i = i + 1
                    random.shuffle(nodes)
                    for node in nodes:
                        n = n + '<a href="/go/' + node.name + '" class="item_node">' + node.title + '</a>'
                        c = c + 1
                s = s + '<div class="sep20"></div><div class="box"><div class="cell"><div class="fr"><strong class="snow">' + section.title_alternative + u'</strong><small class="snow"> • ' + str(section.nodes) + ' nodes</small></div>' + section.title + '</div><div class="inner" align="center">' + n + '</div></div>'
        memcache.set('planes', s, 86400)
        memcache.set('planes_c', c, 86400)

    return (c, s)


def GetMemberRecentNodes(member_num):
    return memcache.get('member::' + str(member_num) + '::recent_nodes')


def GetSiteLandingPageCache():
    return memcache.get('Site::LandingPageCache')

def SetSiteLandingPageCache(site_landingpagecache):
    memcache.set('Site::LandingPageCache', site_landingpagecache, 600)
