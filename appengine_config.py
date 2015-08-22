import os
import sys
import logging
from google.appengine.ext import vendor

# add the 'lib' folder into appengine's python path
try:
    vendor.add('script')
    vendor.add('script/lib')
    logging.info("imported third party library")
except Exception:
    logging.info("cannot import third party library")
