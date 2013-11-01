from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from .utils import GetCurrentCredentials


class OAuth2RequiredMixin(object):
  """Mixin to ensure requests have valid credentials."""

  def dispatch(self, request, *args, **kwargs):
    self.request = request
    self.args = args
    self.kwargs = kwargs

    credentials = GetCurrentCredentials()
    if not credentials:
      # Request a login if not yet authenticated, or unable to refresh.
      return HttpResponseRedirect(reverse("login"))

    return super(OAuth2RequiredMixin, self).dispatch(
      request, *args, **kwargs)
