import httplib2
import logging

from google.appengine.api import users
from oauth2client.appengine import StorageByKeyName, CredentialsModel
from oauth2client.client import AccessTokenRefreshError


def GetCurrentCredentials():
  """Fetch current user's credentials, refreshing if possible."""
  user = users.get_current_user()
  if not user:
    return None

  storage = StorageByKeyName(CredentialsModel, user.user_id(), 'credentials')
  credentials = storage.get()
  if not credentials or not credentials.access_token:
    return None

  if credentials.access_token_expired:
    http = httplib2.Http()
    try:
      logging.info('Refreshing OAuth2 Access Token.')
      credentials.refresh(http)
    except AccessTokenRefreshError:
      return None
    storage.put(credentials)

  return credentials
