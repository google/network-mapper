import re

from django.core.urlresolvers import reverse
from django.test.client import Client

from mock import Mock, patch

from auth.tests import MockedCredentials
from clients.tests.drive_tests import GDRIVE_LIST_RESPONSE
from core.tests.base import BaseAppengineTestCase, MockUser
from graph.models import Graph
from .base import GraphBase


__all__ = [
    'SpreadsheetsLoadingOptionsFormTestCase',
    'GraphCreateTest',
    'GraphUpdateTest',
    'GraphDetailTest',
    'GraphDataTest'
]


class SpreadsheetsLoadingOptionsFormTestCase(BaseAppengineTestCase):

    def setUp(self):
        super(SpreadsheetsLoadingOptionsFormTestCase, self).setUp()
        self.client = Client()

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    def test_fetch_options(self):
        mock = Mock()
        mock.configure_mock(**{
            "files.return_value.list.return_value.execute.return_value": GDRIVE_LIST_RESPONSE})

        with patch("clients.drive.build", return_value=mock):
            response = self.client.get(reverse("spreadsheet_list"))
            self.assertTrue(response.status_code, 200)

            # Only 3 inputs
            self.assertTrue(
                len([
                    m.start() for m in re.finditer(
                        '<input type="radio" name="spreadsheet_id"',
                        response.content
                    )
                ]),
                3
            )
            # Only 3 anchors
            self.assertTrue(
                len([
                    m.start() for m in re.finditer(
                        '<a href="http://example.com/spreadsheet/00[123]" target="_blank">Link</a>',
                        response.content
                    )
                ]),
                3
            )

            self.assertIn("Spreadsheet 001", response.content)
            self.assertIn("Spreadsheet 002", response.content)
            self.assertIn("Spreadsheet 003", response.content)


class GraphCreateTest(GraphBase):

    def setUp(self):
        super(GraphCreateTest, self).setUp()
        self.url = reverse("graph_create")
        self.user = MockUser()

    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    def test_logged_user_should_be_able_to_see_the_page(self):
        self.client.get(reverse("login"))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_should_be_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(str(response).endswith('http://testserver/login\n\n'))

    def test_anonymous_user_should_not_create_a_graph(self):
        response = self.client.post(self.url, data={'name':'Anonymous', 'is_public': True})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(str(response).endswith('http://testserver/login\n\n'))

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user")
    def test_logged_user_should_be_able_to_crate_graph_if_graph_already_exists(self, mocked_user):
        mocked_user.return_value = self.user
        self.create_graph(user_id=self.user.user_id())
        self.client.get(reverse("login"))
        response = self.client.get(reverse("graph_create"))
        self.assertEqual(response.status_code, 200)

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user")
    def test_logged_user_should_be_able_to_create_a_graph(self, mocked_user):
        mocked_user.return_value = self.user
        self.client.get(reverse("login"))
        self.assertFalse(Graph.query(Graph.user_id == self.user.user_id()).get())
        post_data = {'is_public': False, 'name': 'Test', 'spreadsheet_id': '123'}
        response = self.client.post(reverse("graph_create"), post_data)
        self.assertEqual(response.status_code, 302)
        new_graph = Graph.query(Graph.user_id == self.user.user_id()).get()
        self.assertTrue(new_graph)

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user")
    def test_logged_user_should_not_be_able_to_create_a_graph_with_wrong_data(self, mocked_user):
        mocked_user.return_value = self.user
        self.client.get(reverse("login"))
        post_data = {}
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        new_graph = Graph.query(Graph.user_id == self.user.user_id()).get()
        self.assertFalse(new_graph)


class GraphUpdateTest(GraphBase):

    def setUp(self):
        self.user = MockUser()
        super(GraphUpdateTest, self).setUp()
        self.graph = self.create_graph(user_id=self.user.user_id(), is_public=False)
        self.url = reverse("graph_update", args=[self.graph.key.id(), ])

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_logged_user_should_be_able_to_see_the_page(self):
        self.client.get(reverse("login"))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_should_be_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(str(response).endswith('http://testserver/login\n\n'))

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_logged_user_should_not_be_able_to_see_other_user_graph_forms(self):
        self.client.get(reverse("login"))
        response = self.client.get(reverse('graph_update', args=[self.other_public_graph.key.id()]))
        self.assertEqual(response.status_code, 403)

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_logged_user_should_not_be_able_to_update_other_user_graphs(self):
        self.client.get(reverse("login"))
        response = self.client.post(reverse('graph_update', args=[self.other_public_graph.key.id()]), post_data={})
        self.assertEqual(response.status_code, 403)

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user")
    def test_logged_user_should_not_be_able_to_update_a_graph_with_wrong_data(self, mocked_user):
        mocked_user.return_value = self.user
        self.client.get(reverse("login"))
        is_public_value = self.graph.is_public
        post_data = {'is_public': not is_public_value}
        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        graph_not_modified = Graph.query(Graph.user_id == self.user.user_id()).get()
        self.assertEqual(graph_not_modified.is_public, is_public_value)

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_logged_user_should_get_404_if_the_graph_does_not_exist(self):
        self.client.get(reverse("login"))
        res = self.client.get(reverse('graph_update', kwargs={'graph_id': 9999999}))
        self.assertEqual(res.status_code, 404)


class GraphDetailTest(GraphBase):
    def setUp(self):
        self.user = MockUser()
        super(GraphDetailTest, self).setUp()
        self.graph = self.create_graph(user_id=self.user.user_id(), is_public=False)
        self.url = reverse("graph_standalone", args=[self.graph.key.id(), ])

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_logged_user_should_be_able_to_see_page_even_if_the_graph_is_not_public(self):
        self.client.get(reverse("login"))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_should_not_see_the_page_if_the_graph_is_not_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def user_should_see_the_page_if_the_graph_is_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_user_should_get_404_if_the_graph_does_not_exist(self):
        res = self.client.get(reverse('graph_standalone', kwargs={'graph_id': 9999999}))
        self.assertEqual(res.status_code, 404)


class GraphDataTest(GraphBase):

    def setUp(self):
        self.user = MockUser()
        super(GraphDataTest, self).setUp()
        self.graph = self.create_graph(user_id=self.user.user_id(), is_public=False)
        self.url = reverse("graph_data", args=[self.graph.key.id(), ])

    @patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
    @patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
    def test_logged_user_should_be_able_to_access_page_even_if_the_graph_is_not_public(self):
        self.client.get(reverse("login"))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_should_not_see_the_page_if_the_graph_is_not_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def user_should_see_the_page_if_the_graph_is_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_user_should_get_404_if_the_graph_does_not_exist(self):
        res = self.client.get(reverse('graph_standalone', kwargs={'graph_id': 9999999}))
        self.assertEqual(res.status_code, 404)
