from networkx.conf.common import *

# This is the template for the development configuration file. It is loaded by
# settings.py when AppEngine.

# For running locally, i.e. on localhost (not on appspot or a corperate
# appengine), make a copy of this file called `dev.py`. It will only be used
# when running locally.

# For an appspot domain, make a copy of this file which has the same name as
# your appspot application identifier (as specified in the 'application' field
# of the app.yaml file), keeping the postfix `.py`.

# For a corperate domain (i.e. the application field of `app.yaml` is of the
# form `corperate_domain.com:application_id`), make a directory
# `coperate_domain.com`, and copy this file to
# `coperate_domain.com/application_id.py`.

# Turn debug mode on/off.
DEBUG = False

# Fill out these settings
OAUTH_SETTINGS['client_id'] = 'INSERT_YOUR_CLIENT_ID_HERE'
OAUTH_SETTINGS['client_secret'] = 'INSERT_YOUR_CLIENT_SECRET_HERE'
