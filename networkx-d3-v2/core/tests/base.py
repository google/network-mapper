import logging
logger = logging.getLogger(__name__)

import os
import base64

from mock import patch
from ndbtestcase import NdbTestCase
from google.appengine.ext import testbed
from google.appengine.ext import deferred
from oauth2client.appengine import CredentialsModel


class MockedCredentials(CredentialsModel):

    def __init__(self, expired=False):
        self.expired = expired
        self.access_token = 'test'

    @property
    def access_token_expired(self):
        return self.expired

    def refresh(self, http):
        return None

    def authorize(self, http):
        return http


class MockUser(object):

    def __init__(self, user_id='123', email="test@example.com"):
        self._user_id = user_id
        self._email = email

    def set_email(self, e):
        self._email = e

    def set_user_id(self, user_id):
        self._user_id = user_id

    def email(self):
        return self._email

    def user_id(self):
        return self._user_id

mock_user = MockUser()


def mock_get_current_user():
    """ A patch for user.get_current_user
        which always returns our mock user
    """
    return mock_user


class BaseAppengineTestCase(NdbTestCase):
    """ Base testcase which sets up an AppEngine environment
        in order to perform some functional test e.g: with django
        test client

        Includes login/logout helpers which login with the users api
        as well as the standard django auth machinery
    """

    testserver_host = "http://testserver/"

    def setUp(self):

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()

        # Then activate the testbed, which prepares the service stubs
        # for use.
        self.testbed.activate()

        # Create a consistency policy that will simulate the High
        # Replication consistency model.
        #self.policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
        #    probability=0.9)
        # Initialize the datastore stub with this policy.
        #self.testbed.init_datastore_v3_stub(
        #    consistency_policy=self.policy)

        self.testbed.init_datastore_v3_stub()

        # Setup mail stubs
        self.testbed.init_mail_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

        # Setup task queue stub. This will create stubs for
        # each of the queue's in `queue.yaml` If you need
        # something different then ommit the `root_path` arg
        # and create the queue's manually.
        self.testbed.init_taskqueue_stub(root_path='.')
        self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        # Remove the OAuthMiddlware during tests as we don't
        # currently have this mocked.

        from django.conf import settings

        MIDDLEWARE_CLASSES = (
            [m for m in list(settings.MIDDLEWARE_CLASSES)
             if m not in ['google_users_oauth2.middleware.OAuthMiddleware']]
        )

        self.settings_patch = patch.object(
            settings, 'MIDDLEWARE_CLASSES', MIDDLEWARE_CLASSES)

        self.settings_patch.start()

        # AE expects HTTP_HOST to be set.
        os.environ['HTTP_HOST'] = self.testserver_host

        super(BaseAppengineTestCase, self).setUp()

    def tearDown(self):
        self.testbed.deactivate()
        self.settings_patch.stop()
        super(BaseAppengineTestCase, self).tearDown()

    def login(self, username, password, admin=False):
        """ Login a user with the test client and
            the users api.
        """

        # ret = self.client.login(username=username, password=password)

        # if ret:
        #     user = User.objects.get(username=username)
        #     self.testbed.setup_env(
        #         USER_EMAIL=user.email,
        #         USER_IS_ADMIN=admin and '1' or '0',
        #         USER_ID=user.get_profile().gaia_id,
        #         AUTH_DOMAIN='testbed',
        #         overwrite=True
        #     )
        # return ret

        # This won't work for now, but we actually don't need it until we have
        # some kind of User model using NDB
        pass

    def logout(self):
        """ Logout the current user from test client
            and the users api
        """

        for k in ['USER_EMAIL', 'USER_IS_ADMIN', 'USER_ID']:
            if k in os.environ:
                del os.environ[k]
        self.client.logout()

    def run_tasks_in_queue(self, queue_name=None):
        """ Run tasks in the testbed taskqueue stub
        """

        for queue in self.taskqueue_stub.GetQueues():
            if queue_name is None or queue == queue['name']:
                tasks = self.taskqueue_stub.GetTasks(queue['name'])
                for t in tasks:
                    logging.debug('Running task %s from queue %s' % (t['name'], queue['name']))
                    deferred.run(base64.b64decode(t['body']))
                    self.taskqueue_stub.DeleteTask(queue['name'], t['name'])
