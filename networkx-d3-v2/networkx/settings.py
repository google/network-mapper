import os
import logging
from networkx.utils import on_production_server

# By default, if we are running locally, load oauth copnfiguration information
# from this file...
settings_path = os.path.join('conf', 'localhost', 'dev.py')

# If were on the production server, then use the enviroment settings file that
# corresponds to the application id.
if on_production_server:
  from google.appengine.api.app_identity import get_application_id
  full_application_id = get_application_id().lower()

  application_id_parts = full_application_id.split(':')
  if application_id_parts.length == 0 or application_id_parts.length > 2:
    raise Exception('application_id is not valid: it should be non-empty ' +
        'and contain at most one ":" character')

  if application_id_parts.length == 1:
    # If no domain is specified, it is assumed to run on appspot
    domain = 'appspot'
    application_id = application_id_parts[0]
  elif application_id_parts.length == 2:
    domain = application_id_parts[0]
    application_id = application_id_parts[1]

  settings_path = os.path.join('conf', domain, '%s.py' % application_id)

# Execute the path to the environment setting file
if not os.path.exists(settings_path):
  logging.error('Settings file named "%s" does not exist ' +
      '(application_id is %s)' % \
      (settings_path, application_id))
  exit(1)
else:
  logging.info('settings_path is %s' % settings_path)
  execfile(settings_path)
