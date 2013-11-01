import httplib2

from apiclient.discovery import build


class SimpleDriveClient():
    def __init__(self, credentials):
        """
        We expect some OAuth2 credentials that allow us to authorize the user,
        so we assume that the access_token is valid. Is the caller's
        responsability to refresh the tokens if needed.
        """
        self.credentials = credentials
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.service = build("drive", "v2", http=http)

    # TODO: remove this; it is not used.
    def get_spreadsheet_list(self):
        """
        For now it only fetchs the first 100 elements,
        we might need to make some calls using nextLink attribute
        of the response
        """
        response = self.service.files().list().execute()
        mimeType = "application/vnd.google-apps.spreadsheet"
        spreadsheets = []
        for item in response["items"]:
            if item["mimeType"] == mimeType:
                spreadsheets.append(item)

        return spreadsheets
