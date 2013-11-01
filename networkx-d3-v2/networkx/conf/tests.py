from networkx.conf.common import *

APP_ID = "networkx-testing"

# Enable debuging
DEBUG = True
TEMPLATE_DEBUG = True

HOSTNAME = "http://testserver"

TEST_RUNNER = 'networkx.testrunner_nodb.TestRunnerNoDb'

import logging
logging.disable(logging.CRITICAL)
