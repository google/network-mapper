import os
import sys
import logging
sys.path.extend(['lib'])

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

os.environ['APPENGINE_PRODUCTION'] = \
    os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or\
    os.getenv('SETTINGS_MODE') == 'prod'

import django
import django.core.signals
import django.dispatch
import django.db

if not os.getenv('APPENGINE_PRODUCTION'):
    logging.info('Development django: %s' % django.__file__)
    logging.info(django.get_version())


# Log exceptions
def log_exception(*args, **kwds):
    logging.exception('Exception in request:')

django.dispatch.Signal.connect(
    django.core.signals.got_request_exception, log_exception)

# WSGI app
import django.core.handlers.wsgi
app = django.core.handlers.wsgi.WSGIHandler()
