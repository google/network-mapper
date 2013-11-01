from mock import Mock, patch

from auth.tests import MockedCredentials
from core.tests.base import BaseAppengineTestCase
from ..drive import SimpleDriveClient


GDRIVE_LIST_RESPONSE = {
    "items": [
        {
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "title": "Spreadsheet 001",
            "id": "01235678",
            "alternateLink": "http://example.com/spreadsheet/001"
        },
        {
            "mimeType": "image/png",
            "title": "Cadiz view",
            "id": "14692"
        },
        {
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "title": "Spreadsheet 002",
            "id": "58623423",
            "alternateLink": "http://example.com/spreadsheet/002"
        },
        {
            "mimeType": "application/vnd.google-apps.spreadsheet",
            "title": "Spreadsheet 003",
            "id": "9876",
            "alternateLink": "http://example.com/spreadsheet/003"
        }
    ]
}


__all__ = [
    'DriveClientTestCase'
]


class DriveClientTestCase(BaseAppengineTestCase):

    def test_client_init(self):
        client = SimpleDriveClient(MockedCredentials())
        self.assertIsNotNone(client)
        self.assertEqual(client.service.__class__.__name__, "Resource")

    def test_spreadsheet_fetching(self):
        mock = Mock()
        mock.configure_mock(**{
            "files.return_value.list.return_value.execute.return_value": GDRIVE_LIST_RESPONSE})

        with patch("clients.drive.build", return_value=mock):
            client = SimpleDriveClient(MockedCredentials())
            spreadsheets = client.get_spreadsheet_list()
            self.assertTrue(len(spreadsheets), 3)
            self.assertEqual(
                [item["title"] for item in spreadsheets],
                ["Spreadsheet 001", "Spreadsheet 002", "Spreadsheet 003"]
            )
