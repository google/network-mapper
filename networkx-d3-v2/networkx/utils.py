import sys
import os
import re
from distutils.version import StrictVersion

host_rx = re.compile('^(localhost|(?:\d+\.\d+\.\d+\.\d+))(?:\:(\d+))?')


# Are we running live on a appsot instance ? Using this
# instead of the test in djangoappengine as it mistakenly
# returns true when datastore stubs are available and
# os.environ['SERVER_SOFTWARE'] is empty
on_production_server = 'google' in \
    os.environ.get('SERVER_SOFTWARE', '').lower()


def customize_path():
  """ Add our extra library paths to sys.path
  """
  extra_paths = [
    'lib'
  ]
  for lib in extra_paths:
    if not lib in sys.path:
      sys.path.insert(0, lib)


def fix_path():
  """ Set up the python path using dev_appserver """

  sdk_path, test_path = '', ''

  for path in os.environ.get('PATH').split(os.pathsep):
    # We except an OSError as there could be a
    # non-existent path in $PATH which would cause
    # listdir to fail. This is apparent on cloudbees
    # jenkins for example.
    try:
      if 'dev_appserver.py' in os.listdir(path):
        test_path = os.path.join(path, 'dev_appserver.py')
        sdk_path = os.path.dirname(os.readlink(test_path)
          if os.path.islink(test_path)
          else test_path)
        sys.path.insert(0, sdk_path)
        from dev_appserver import fix_sys_path, GOOGLE_SQL_EXTRA_PATHS
        fix_sys_path(extra_extra_paths=GOOGLE_SQL_EXTRA_PATHS)
        customize_path()
    except OSError:
      continue


def setup_appengine_env():
  """ Setup the environment when running outside of dev_appserver
  """

  default_host, default_port = '127.0.0.1', '8000'

  if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'networkx.settings'

  fix_path()

  import google
  from google import appengine
  from google.appengine.tools.dev_appserver_main import DEFAULT_ARGS

  # Set some environment vars that are usually set by
  # dev_appserver eg host and port ..

  matches = host_rx.match(sys.argv[-1])
  arg_host, arg_port = matches and matches.groups() or (None, None)
  host = arg_host or default_host
  port = arg_port or default_port

  if 'SERVER_NAME' not in os.environ:
    os.environ['SERVER_NAME'] = host + ':' + port

  if 'SERVER_PORT' not in os.environ:
    os.environ['SERVER_PORT'] = port

  option_dict = DEFAULT_ARGS.copy()

  # Always use the high replication datastore model
  option_dict.update({
    'high_replication': True
  })

  # Load Config from app.yaml
  root_path = '.'
  root_path = os.path.normpath(os.path.abspath(root_path))
  default_partition = 'dev'
  config, _, _ = appengine.tools.dev_appserver.LoadAppConfig(root_path, {},
      default_partition=default_partition)
  appengine.tools.dev_appserver.SetupStubs(config.application, **option_dict)

  if config.libraries:
    sdk_path = os.path.dirname(os.path.dirname(google.__file__))
    extra_paths = []
    for library in config.libraries:
      version = library.version
      if library.version == "latest":
        version = appengine.api.appinfo._NAME_TO_SUPPORTED_LIBRARY[library.name].non_deprecated_versions[-1]
      if StrictVersion(appengine.tools.dev_appserver.GetVersionObject()["release"]) < StrictVersion("1.7.5"):
        p = os.path.join(sdk_path, 'lib', library.name + '_' + version.replace('.', '_'))
      else:
        p = os.path.join(sdk_path, 'lib', library.name + '-' + version)
      extra_paths.append(p)
    if extra_paths:
      sys.path = extra_paths + sys.path
