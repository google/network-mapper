from mock import Mock, patch

from core.tests.base import MockUser
from auth.tests import MockedCredentials
from .base import GraphBase
from graph.models import Node, ErrorLog, Style
from ..utils import generate_nodes_through_spreadsheet


GOOD_NODES = [
    {
        "name": "Bruce Dickinson",
        "categories": "Metal",
        "importance": "5",
        "short_description": None,
        "long_description": None,
        "context_url": None,
        "credit": None,
        "node_style": None,
        "label_style": None,
    },
    {
        "name": "Rob Halford",
        "categories": "Metal",
        "importance": "6",
        "short_description": "Judas Priest's singer",
        "long_description": None,
        "context_url": None,
        "credit": None,
        "node_style": None,
        "label_style": None,
    },
    {
        "name": "Freddie Mercury",
        "categories": "Pop,Rock",
        "importance": "10",
        "short_description": None,
        "long_description": None,
        "context_url": "http://www.freddiemercury.com/",
        "credit": "Foo",
        "node_style": "a-style",
        "label_style": "b-style",
    }
]

BAD_NODES = [{
    "name": "Justin Bieber",
    "categories": "noise",
    "importance": "-100",
    "short_description": None,
    "long_description": None,
    "context_url": "not a url",
    "credit": None,
    "node_style": None,
    "label_style": None,
}]

ALL_NODES = GOOD_NODES + BAD_NODES
FETCHED_CATEGORIES = [
    {
        'name': 'Pop',
        'node_style': '',
        'label_style': '',
    },
    {
        'name': 'Rock',
        'node_style': '',
        'label_style': '',
    },
    {
        'name': 'Metal',
        'node_style': '',
        'label_style': '',
    }
]

FETCHED_STYLES = {
    'a-class': [
        'font-size: 10px;',
        'font-family: verdana',
    ],
    'b-class': [
        'border: 1px solid green;'
    ]
}

__all__ = [
    'TestGenerateNodesThroughSpreadsheet',
]


@patch("google.appengine.api.users.get_current_user", Mock(return_value=MockUser()))
@patch("oauth2client.appengine.StorageByKeyName.get", Mock(return_value=MockedCredentials()))
class TestGenerateNodesThroughSpreadsheet(GraphBase):

    def setUp(self):
        super(TestGenerateNodesThroughSpreadsheet, self).setUp()
        self.user = MockUser()
        self.graph = self.create_graph(user_id=self.user.user_id(), is_public=True)

    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_nodes", Mock(return_value=GOOD_NODES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.GetCategories", Mock(return_value=FETCHED_CATEGORIES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_styles", Mock(return_value=FETCHED_STYLES))
    def test_generate_nodes_with_good_data(self):
        self.assertEqual(0, ErrorLog.query().count())
        self.assertEqual(0, Node.query().count())
        self.assertEqual(0, Style.query().count())
        generate_nodes_through_spreadsheet(graph=self.graph)
        self.assertEqual(len(GOOD_NODES), Node.query(Node.is_category == True).count())
        self.assertEqual(len(FETCHED_CATEGORIES), Node.query(Node.is_category == False).count())
        self.assertEqual(1, Style.query(Style.graph == self.graph.key).count())
        self.assertEqual(0, ErrorLog.query().count())

        # now let's check ALL THE DATA
        node_1 = Node.query(Node.name == "Bruce Dickinson").get()
        self.assertEqual(node_1.name, "Bruce Dickinson")
        self.assertEqual(','.join([category.get().name for category in node_1.categories]), "Metal")
        self.assertEqual(node_1.importance, 5)
        self.assertEqual(node_1.short_description, None)
        self.assertEqual(node_1.long_description, None)
        self.assertEqual(node_1.context_url, None)
        self.assertEqual(node_1.credit, None)
        self.assertEqual(node_1.node_style, None)
        self.assertEqual(node_1.label_style, None)

        node_2 = Node.query(Node.name == "Rob Halford").get()
        self.assertEqual(node_2.name, "Rob Halford")
        self.assertEqual(','.join([category.get().name for category in node_2.categories]), "Metal")
        self.assertEqual(node_2.importance, 6)
        self.assertEqual(node_2.short_description, "Judas Priest's singer")
        self.assertEqual(node_2.long_description, None)
        self.assertEqual(node_2.context_url, None)
        self.assertEqual(node_2.credit, None)
        self.assertEqual(node_2.node_style, None)
        self.assertEqual(node_2.label_style, None)

        node_3 = Node.query(Node.name == "Freddie Mercury").get()
        self.assertEqual(node_3.name, "Freddie Mercury")
        self.assertEqual(','.join([category.get().name for category in node_3.categories]), "Pop,Rock")
        self.assertEqual(node_3.importance, 10)
        self.assertEqual(node_3.short_description, None)
        self.assertEqual(node_3.long_description, None)
        self.assertEqual(node_3.context_url, "http://www.freddiemercury.com/")
        self.assertEqual(node_3.credit, "Foo")
        self.assertEqual(node_3.node_style, "a-style")
        self.assertEqual(node_3.label_style, "b-style")

        style = Style.query(Style.graph == self.graph.key).get()
        self.assertEqual(
            style.styles,
            '.a-class { font-size: 10px; font-family: verdana }\n.b-class { border: 1px solid green; }'
        )

    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_nodes", Mock(return_value=ALL_NODES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.GetCategories", Mock(return_value=FETCHED_CATEGORIES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_styles", Mock(return_value=FETCHED_STYLES))
    def test_generate_nodes_with_good_and_bad_data(self):
        self.assertEqual(0, ErrorLog.query().count())
        self.assertEqual(0, Node.query().count())
        generate_nodes_through_spreadsheet(graph=self.graph)
        self.assertEqual(len(GOOD_NODES), Node.query(Node.is_category == True).count())
        self.assertEqual(len(FETCHED_CATEGORIES), Node.query(Node.is_category == False).count())
        self.assertEqual(1, Style.query(Style.graph == self.graph.key).count())
        self.assertEqual(1, ErrorLog.query().count())

    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_nodes", Mock(return_value=GOOD_NODES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.GetCategories", Mock(return_value=[]))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_styles", Mock(return_value=FETCHED_STYLES))
    def test_try_to_generate_nodes_without_any_category(self):
        self.assertEqual(0, ErrorLog.query().count())
        self.assertEqual(0, Node.query().count())
        generate_nodes_through_spreadsheet(graph=self.graph)
        self.assertEqual(0, Node.query().count())
        self.assertEqual(1, ErrorLog.query().count())
        self.assertEqual(1, Style.query(Style.graph == self.graph.key).count())

    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_nodes", Mock(return_value=GOOD_NODES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.GetCategories", Mock(return_value=FETCHED_CATEGORIES))
    @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_styles", Mock(return_value=FETCHED_STYLES))
    def test_all_graph_related_entities_should_be_deleted_before_updating_the_graph(self):
        self.assertEqual(0, ErrorLog.query().count())
        self.assertEqual(0, Node.query().count())
        self.assertEqual(0, Style.query().count())
        generate_nodes_through_spreadsheet(graph=self.graph)
        categories_before = Node.query(Node.is_category == True).count()
        nodes_before = Node.query(Node.is_category == False).count()
        style_before = Style.query(Style.graph == self.graph.key).count()
        logs_before = ErrorLog.query().count()
        generate_nodes_through_spreadsheet(graph=self.graph)
        self.assertEqual(categories_before, Node.query(Node.is_category == True).count())
        self.assertEqual(nodes_before, Node.query(Node.is_category == False).count())
        self.assertEqual(style_before, Style.query(Style.graph == self.graph.key).count())
        self.assertEqual(logs_before, ErrorLog.query().count())
