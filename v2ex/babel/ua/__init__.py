# coding=utf-8

import re
import os
import logging
from user_agents import parse

def detect(request):
    """
    parse the User-Agent from the browser
    """
    ua_string = request.headers['User-Agent']
    logging.info("User-Agent: " + ua_string)
    user_agent = parse(ua_string)
    return user_agent

