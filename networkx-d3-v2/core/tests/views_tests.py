from django.test.client import Client
from django.core.urlresolvers import reverse
from mock import Mock, patch

from .base import BaseAppengineTestCase, MockUser, MockedCredentials


__all__ = [
    'HomePageTest'
]


class HomePageTest(BaseAppengineTestCase):

    def setUp(self):
        super(HomePageTest, self).setUp()
        self.client = Client()
        self.client.session['credientials'] = 'credentials'

    def test_anonymous_user_should_be_able_view_the_homepage(self):
        response = self.client.get(reverse("homepage"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('login', str(response))

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    def test_logged_user_should_be_able_view_the_homepage_with_custom_content(self):
        self.client.get(reverse("login"))
        response = self.client.get(reverse("homepage"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('logout', str(response))
