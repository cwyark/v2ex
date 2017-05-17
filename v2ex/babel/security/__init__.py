# coding=utf-8

import os
import hashlib
import logging

from google.appengine.ext import db
from google.appengine.api import memcache

from v2ex.babel.ext.cookies import Cookies

def CheckAuth(handler):
    ip = handler.request.remote_addr
    cookies = handler.request.cookies
    if 'auth' in cookies:
        auth = cookies['auth']
        member_num = memcache.get(auth)
        if member_num > 0:
            member = memcache.get('Member_' + str(member_num))
            if member is None:
                q = db.GqlQuery("SELECT * FROM Member WHERE num = :1", member_num)
                if q.count() == 1:
                    member = q[0]
                    memcache.set(auth, member.num)
                    memcache.set('Member_' + str(member_num), member)
                else:
                    member = None
            if member:
                member.ip = ip
            return member
        else:
            q = db.GqlQuery("SELECT * FROM Member WHERE auth = :1", auth)
            if (q.count() == 1):
                member_num = q[0].num
                member = q[0]
                memcache.set(auth, member_num)
                memcache.set('Member_' + str(member_num), member)
                member.ip = ip
                return member
            else:
                return None
    else:
        return None
