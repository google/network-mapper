"""
WSGI config for Network Mapper.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys
import logging
import google.storage.speckle.python.django.backend

from networkx.utils import customize_path
customize_path()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'networkx.settings')

# I don't understand how this ever worked without the exception handler- would
# always return True or False, which will throw:
#  File "/proj/potato/networkx/lib64/python2.7/os.py", line 471, in __setitem__
#  putenv(key, item)
# TypeError: must be string, not bool
try:
  os.environ['APPENGINE_PRODUCTION'] = \
      os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or\
      os.getenv('SETTINGS_MODE') == 'prod'
except TypeError:
  os.environ['APPENGINE_PRODUCTION'] = ''

import django
import django.core.signals
import django.dispatch

if not os.getenv('APPENGINE_PRODUCTION'):
  logging.info('Development django (%s): %s',
               django.get_version(), django.__file__)

# Log exceptions
def log_exception(*args, **kwds):
  logging.exception('Exception in request:')

django.dispatch.Signal.connect(
  django.core.signals.got_request_exception, log_exception)

# Media Generator
if os.environ.get('SERVER_SOFTWARE', '').lower().startswith('devel'):
  try:
    from google.appengine.api.mail_stub import subprocess
    sys.modules['subprocess'] = subprocess
    import inspect
    frame = inspect.currentframe().f_back.f_back.f_back
    old_builtin = frame.f_locals['old_builtin']
    subprocess.buffer = old_builtin['buffer']
  except Exception, e:
    import logging
    logging.warn('Could not add the subprocess module to the sandbox: %s' % e)

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
