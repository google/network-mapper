from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


def google_login_required(view_func):
  """
  Decorator that simulates the Django's @login_required, but
  using Google Users API.
  """
  def wrap(request, *args, **kwargs):
    if request.session.get("credentials", None):
      return view_func(request, *args, **kwargs)
    else:
      return HttpResponseRedirect(reverse("login"))

  return wrap
