"""Oauth handlers."""

import pickle
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from google.appengine.api import users
from google.appengine.api import memcache
from oauth2client.appengine import StorageByKeyName, CredentialsModel
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError

from .utils import GetCurrentCredentials

logger = logging.getLogger(__name__)


def login(request):
  user = users.get_current_user()

  if not user:
    logger.info("User not registered, Forcing login with users api.")
    return HttpResponseRedirect(users.create_login_url(
      request.get_full_path()))

  credentials = GetCurrentCredentials()
  if not credentials:
    return HttpResponseRedirect(reverse("oauth2redirect"))

  request.session['credentials'] = credentials
  return HttpResponseRedirect(reverse("homepage"))


def __initial_oauth_flow(request, approval_prompt='auto'):
  flow = OAuth2WebServerFlow(
    # Visit https://code.google.com/apis/console to
    # generate your client_id, client_secret and to
    # register your redirect_uri.
    client_id=settings.OAUTH_SETTINGS['client_id'],
    client_secret=settings.OAUTH_SETTINGS['client_secret'],
    scope=settings.OAUTH_SETTINGS['scopes'],
    user_agent=settings.OAUTH_SETTINGS['user_agent'],
    approval_prompt=approval_prompt,
    redirect_uri=settings.OAUTH_SETTINGS['redirect_uri'],
    access_type="online"
  )

  # Generate the URL to oauth with passing the redirect URI.
  # Redirect URL must be obtained from the request.META, which gets passed
  # a threadsafe environ (from the wsgi handler) and not from os.environ
  authorize_url = flow.step1_get_authorize_url()

  # As suggested on the documentation, we store the flow on memcache
  user = users.get_current_user()
  memcache.set(user.user_id(), pickle.dumps(flow))

  request.session['redirect'] = request.GET.get('redirect', '/')

  return HttpResponseRedirect(authorize_url)


def oauth2redirect(request):
  user = users.get_current_user()
  storage = StorageByKeyName(CredentialsModel, user.user_id(), 'credentials')
  credentials = storage.get()

  # if not credentials or not credentials.refresh_token:
    # return __initial_oauth_flow(request, approval_prompt='force')
  # Use approval_prompt='force' to ensure the refresh token is good.
  return __initial_oauth_flow(request, approval_prompt='force')


def oauth2callback(request):
  user = users.get_current_user()
  flow = pickle.loads(memcache.get(user.user_id()))

  try:
    credentials = flow.step2_exchange(request.GET)
    request.session['credentials'] = credentials
    storage = StorageByKeyName(CredentialsModel, user.user_id(), 'credentials')
    storage.put(credentials)
    redirect = request.session.get('redirect', '/')
    return HttpResponseRedirect(redirect)
  except FlowExchangeError:
    logger.exception('Failed to authenticate')

  return HttpResponseRedirect(reverse(settings.OAUTH_FAILED_REDIRECT))


def oauth2logout(request):
  for key in settings.OAUTH_SESSION_KEYS:
    if key in request.session:
      del request.session[key]

  redirect = request.session.get('redirect', '/')
  return HttpResponseRedirect(redirect)


def auth_failed(request):
  return HttpResponse("Something went wrong with your OAuth")
