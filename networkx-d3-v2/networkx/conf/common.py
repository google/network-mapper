import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

DEBUG = False
TEMPLATE_DEBUG = DEBUG


VERSION = os.environ.get('CURRENT_VERSION_ID', '').split('.')[0]
HOSTNAME = 'http://%s' % os.environ.get('HTTP_HOST', '').replace("%s." % VERSION, "")


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# A custom cache backend using AppEngine's memcached
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'TIMEOUT': 15 * 60,
    }
}

"""
Custom session engine using our cache or writing through to the datastore If
using SQL, can we use django's standard write through?  If gae memecached is
stable enough, it would be faster to use
django.contrib.sessions.backends.cache?
"""

SESSION_ENGINE = "appengine_sessions.backends.cached_db"

# Uncomment these DB definitions to use Cloud SQL.
# See: https://developers.google.com/cloud-sql/docs/django#development-settings
#import os
#if (os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine') or
#    os.getenv('SETTINGS_MODE') == 'prod'):
#    # Running on production App Engine, so use a Google Cloud SQL database.
#    DATABASES = {
#        'default': {
#            'ENGINE': 'google.appengine.ext.django.backends.rdbms',
#            'INSTANCE': 'my_project:instance1',
#            'NAME': 'my_db',
#            }
#        }
#else:
#    # Running in development, so use a local MySQL database.
#    DATABASES = {
#        'default': {
#            'ENGINE': 'django.db.backends.sqlite3',
##            'USER': 'root',
##            'PASSWORD': '',
##            'HOST': 'localhost',
#            'NAME': 'my_db',
#            }
#        }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Use the new automatic timezone features Django 1.4 brings
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/staticfiles/"
STATIC_ROOT = os.path.join(PROJECT_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^(&s11q!@t2j@=dgpp65k+df6o1(@1h9cq-$^p@=k4!5))xi6u'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'google.appengine.ext.ndb.django_middleware.NdbDjangoMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

INTERNAL_IPS = ('127.0.0.1',)

ROOT_URLCONF = 'networkx.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'networkx.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'templates'),

)

INSTALLED_APPS = (
    # 'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'graph',
    'clients',
    'auth',
    'appengine_sessions',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.request",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "auth.context_processors.google_user"
)

FIXTURE_DIRS = (
    os.path.join(PROJECT_DIR, 'fixtures'),
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

HOSTNAME = 'http://%s' % os.environ.get('HTTP_HOST')


# Google oauth settings
OAUTH_SETTINGS = {
    'client_id': 'client_id',  # overwrite on the specific settings file
    'client_secret': 'client_secret',  # overwrite on the specific settings file
    'redirect_uri': '%s/oauth2callback' % HOSTNAME,
    'scopes': [
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/drive.readonly',
        'https://spreadsheets.google.com/feeds/'
    ],
    'login_url': 'https://accounts.google.com/o/oauth2/auth',
    'token_url': 'https://accounts.google.com/o/oauth2/token',
    'user_agent': 'appengine/networkx'
}

OAUTH_DEFAULT_REDIRECT = 'home'
OAUTH_FAILED_REDIRECT = 'auth-failed'

OAUTH_SESSION_KEYS = [
    'user',
    'credentials',
    'flow',
    'request_token',
    'auth_service'
]
