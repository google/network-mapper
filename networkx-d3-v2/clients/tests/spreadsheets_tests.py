from gdata.spreadsheets.client import SpreadsheetsClient
from mock import Mock, patch

from auth.tests import MockedCredentials
from core.tests.base import BaseAppengineTestCase
from ..spreadsheets import SimpleSpreadsheetsClient

__all__ = [
  'SpreadsheetClientTestCase'
]


class MockWorksheets(Mock):

  def __init__(self, worksheets, *args, **kwargs):
    super(MockWorksheets, self).__init__(*args, **kwargs)
    sub_mocks = []
    for worksheet_name, worksheet_id in worksheets:
      mock = Mock()
      mock.configure_mock(**{
        "title.text": worksheet_name,
        "get_worksheet_id.return_value": worksheet_id
      })
      sub_mocks.append(mock)
    self.entry = sub_mocks


class MockCells(Mock):

  def __init__(self, cells, *args, **kwargs):
    super(MockCells, self).__init__(*args, **kwargs)
    sub_mocks = []

    for cell_id, cell_name in cells:
      if cell_name:
        mock = Mock()
        mock.configure_mock(**{
          "id.text": SPREADSHEET_URL_FORMAT % cell_id,
          "content.text": cell_name
        })
        sub_mocks.append(mock)
    self.entry = sub_mocks


SPREADSHEET_URL_FORMAT = "https://spreadsheets.google.com/feeds/cells/sp_id/ws_id/%s"

NODES_HEADER = [
  ("R1C1", "NAME"),
  ("R1C2", "CATEGORIES"),
  ("R1C3", "IMPORTANCE"),
  ("R1C4", "SHORT DESCRIPTION"),
  ("R1C5", "LONG DESCRIPTION"),
  ("R1C6", "CONTEXT URL"),
  ("R1C7", "CREDIT"),
  ("R1C8", "NODE_STYLE"),
  ("R1C9", "LABEL_STYLE"),
]

NODES_ROW_1 = [
  ("R2C1", "Bruce Dickinson"),
  ("R2C2", "Metal"),
  ("R2C3", "5"),
  ("R2C4", None),
  ("R2C5", None),
  ("R2C6", None),
  ("R2C7", None),
  ("R2C8", None),
  ("R2C9", None),
]

NODES_ROW_2 = [
  ("R3C1", "Rob Halford"),
  ("R3C2", "Metal"),
  ("R3C3", "6"),
  ("R3C4", "Judas Priest's singer"),
  ("R3C5", None),
  ("R3C6", None),
  ("R3C7", None),
  ("R3C8", None),
  ("R3C9", None),
]

NODES_ROW_3 = [
  ("R4C1", "Freddie Mercury"),
  ("R4C2", "Pop,Rock"),
  ("R4C3", "10"),
  ("R4C4", None),
  ("R4C5", None),
  ("R4C6", "http://www.freddiemercury.com/"),
  ("R4C7", "Foo"),
  ("R4C8", "a-style"),
  ("R4C9", "b-style"),
]

FULL_NODES = NODES_HEADER + NODES_ROW_1 + NODES_ROW_2 + NODES_ROW_3

NODES_OUT_OF_SCOPE = [
  ("R3C11", "Testing 001"),
  ("R4C12", "Testing 002"),
]

CATEGORIES = [
  ("R1C1", "NAME"), ("R1C2", "NODE-STYLE"), ("R1C3", "LABEL-STYLE"),
  ("R2C1", "Category 001"), ("R2C2", "node-style-001"), ("R2C3", "label-style-001"),
  ("R3C1", "Category 002"), ("R3C2", "node-style-002"), ("R3C3", "label-style-002"),
  ("R4C1", "Category 003"), ("R4C2", "node-style-003"), ("R4C3", "label-style-003"),
]

STYLES = [
  ("R1C1", "CLASSNAME"), ("R1C2", "STYLES"),
  ("R2C1", "class-name"), ("R2C2", "border: 1px solid green;"),
  ("R3C1", ".another-class"), ("R3C2", "border: 2px solid pink;"),
  ("R4C1", "class-name"), ("R4C2", "height: 100%;"),
]


class SpreadsheetClientTestCase(BaseAppengineTestCase):

  def setUp(self):
    super(SpreadsheetClientTestCase, self).setUp()
    self.credentials = MockedCredentials()
    self.client = SimpleSpreadsheetsClient(self.credentials)
    self.spreadsheet_id = '1234567890'

  def _generate_worksheets_mocks(self, tabs_names):
    sub_mocks = []
    for tab in tabs_names:
      mock = Mock()
      mock.configure_mock(**{"title.text": tab})
      sub_mocks.append(mock)
    return Mock(entry=sub_mocks)

  def test_proper_client_init(self):
    self.assertIsNotNone(self.client)
    self.assertIsInstance(self.client, SimpleSpreadsheetsClient)
    self.assertIsInstance(self.client, SpreadsheetsClient)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("Tab002", "456"), ("Tab003", "789")])))
  def test_no_categories_worksheet(self):
    categories = self.client.GetCategories(self.spreadsheet_id)
    self.assertEqual(len(categories), 0)

    nodes = self.client.GetNodes(self.spreadsheet_id)
    self.assertEqual(len(nodes), 0)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([])))
  def test_none_worksheets(self):
    categories = self.client.GetCategories(self.spreadsheet_id)
    self.assertEqual(len(categories), 0)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("CATEGORIES", "456"), ("Tab003", "789")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells([])))
  def test_no_categories(self):
    categories = self.client.GetCategories(self.spreadsheet_id)
    self.assertEqual(len(categories), 0)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("CATEGORIES", "456"), ("Tab003", "789")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells(CATEGORIES)))
  def test_categories(self):
    categories = self.client.GetCategories(self.spreadsheet_id)
    self.assertEqual(
      categories,
      [
        {
          'label_style': 'label-style-001',
          'name': 'Category 001',
          'node_style': 'node-style-001'
        },
        {
          'label_style': 'label-style-002',
          'name': 'Category 002',
          'node_style': 'node-style-002'
        },
        {
          'label_style': 'label-style-003',
          'name': 'Category 003',
          'node_style': 'node-style-003'
        }
      ]
    )

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("Tab002", "456"), ("Tab003", "789")])))
  def test_no_nodes_worksheet(self):
    nodes = self.client.GetNodes(self.spreadsheet_id)
    self.assertEqual(len(nodes), 0)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("CATEGORIES", "456"), ("NODES", "789")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells([])))
  def test_no_nodes(self):
    nodes = self.client.GetNodes(self.spreadsheet_id)
    self.assertEqual(len(nodes), 0)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("CATEGORIES", "456"), ("NODES", "789")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells(NODES_HEADER)))
  def test_no_nodes_only_headers(self):
    nodes = self.client.GetNodes(self.spreadsheet_id)
    self.assertEqual(len(nodes), 0)

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("CATEGORIES", "456"), ("NODES", "789")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells(FULL_NODES)))
  def test_full_nodes(self):
    nodes = self.client.GetNodes(self.spreadsheet_id)
    self.assertEqual(nodes,
      [
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
    )

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("Tab001", "123"), ("CATEGORIES", "456"), ("NODES", "789")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells(FULL_NODES + NODES_OUT_OF_SCOPE)))
  def test_full_nodes_with_errors(self):
    nodes = self.client.GetNodes(self.spreadsheet_id)
    self.assertEqual(nodes,
      [
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
    )

  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_worksheets",
    Mock(return_value=MockWorksheets([
      ("STYLES", "123")])))
  @patch("clients.spreadsheets.SimpleSpreadsheetsClient.get_cells",
    Mock(return_value=MockCells(STYLES)))
  def test_styles(self):
    styles = self.client.get_styles(self.spreadsheet_id)
    self.assertEqual(
      styles,
      {
        'class-name': [
          'border: 1px solid green;',
          'height: 100%;',
        ],
        'another-class': [
          'border: 2px solid pink;'
        ]
      }
    )
