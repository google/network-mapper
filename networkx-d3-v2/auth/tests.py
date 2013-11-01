from django.core.urlresolvers import reverse
from django.test.client import Client

from mock import Mock, patch

from core.tests.base import BaseAppengineTestCase, MockUser, MockedCredentials


class AuthTestCase(BaseAppengineTestCase):

    def setUp(self):
        super(AuthTestCase, self).setUp()
        self.client = Client()

    def test_login_without_google_user(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://testserver/_ah/login?continue=', str(response))

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_user_without_credentials(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://testserver/oauth2redirect', str(response))

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    def test_user_with_credentials(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(str(response).endswith('http://testserver/\n\n'))
        self.assertIsInstance(self.client.session["credentials"], MockedCredentials)

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials(True)))
    @patch("oauth2client.appengine.StorageByKeyName.put", Mock(return_value=lambda x: None))
    def test_user_with_expired_credentials(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(str(response).endswith('http://testserver/\n\n'))
        self.assertIsInstance(self.client.session["credentials"], MockedCredentials)

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_user_starts_oauth2_flow(self):
        response = self.client.get(reverse("oauth2redirect"))
        self.assertEqual(response.status_code, 302)
        self.assertIn('https://accounts.google.com/o/oauth2/auth?redirect_uri=', str(response))
        self.assertEqual(self.client.session["redirect"], "/")

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    @patch("oauth2client.client.OAuth2WebServerFlow.step2_exchange", Mock(return_value=MockedCredentials()))
    @patch("oauth2client.appengine.StorageByKeyName.put", Mock(return_value=lambda x: None))
    def test_user_oauth2_callback(self):
        response = self.client.get(reverse("oauth2redirect"))
        response = self.client.get(reverse("oauth2callback"), {"code": "1234"})
        self.assertEqual(response.status_code, 302)
        self.assertIsInstance(self.client.session["credentials"], MockedCredentials)
        self.assertTrue(str(response).endswith('http://testserver/\n\n'))

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_user_oauth2_callback_failed(self):
        response = self.client.get(reverse("oauth2redirect"))
        response = self.client.get(reverse("oauth2callback"), {"code": "1234"})
        self.assertEqual(response.status_code, 302)
        self.assertIn('http://testserver/auth-failed', str(response))
