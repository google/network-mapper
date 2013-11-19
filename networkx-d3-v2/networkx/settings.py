import os
import logging
from networkx.utils import on_production_server

# Load the settings file from the selected environment
# eg if locally `NETWORKX_ENV` is set to 'ardvark_party' then we would
# attempt to load the settings file `conf/ardvark_party.py`
# If the app is deployed as someapp.appspot.com then we would
# attempt to load the settings file `conf/someapp.py
# If NETWORKX_ENV is not set, and it's not on a production server, then
# env_name is 'dev' and setting are loaded from 'networkx/conf/dev.py'

# Get the current networkx environment name and default to 'dev' if none set.
env_name = os.environ.get('NETWORKX_ENV', 'dev')

# If were on the production server, then use the enviroment settings file that
# corresponds to the appid.
if on_production_server:
  from google.appengine.api.app_identity import get_application_id
  env_name = get_application_id().lower()

# Construct the path
if env_name.startswith('google.com:'):
  env_name = env_name.replace('google.com:', '')
  settings_path = os.path.join('networkx', 'conf', 'google', '%s.py' % env_name)
else:
  settings_path = os.path.join('networkx', 'conf', '%s.py' % env_name)

# Execute the path to the environment setting file
if not os.path.exists(settings_path):
  logging.error('Settings file named %s does not exist (env_name is %s)' % \
      (settings_path, env_name))
  exit(1)
else:
  logging.info('Env %s' % env_name)
  execfile(settings_path)


# If the app is not deployed then allow importing of a `local_settings.py`
# file to allow some customization, eg custom logging settings etc..
# if not on_production_server:
  # try:
    # from settings_local import *
  # except ImportError as e:
    # logging.info('NOTE: no local_settings.py file set: %s' % e)
