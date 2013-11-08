"""All primary UI view handlers."""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.generic import View, TemplateView, FormView
from google.appengine.api import users

from models import Vis
from forms import VisForm


def _fetchIndex():
  """Obtain list of all visualizations."""
  user = users.get_current_user()
  logging.info('Fetching index for user %s', user.user_id())
  try:
    query = Vis.query(Vis.user_id == user.user_id())
  except AttributeError:
    query = None
  index = []
  if query:
    index = [vis.to_dict() for vis in query.iter()]
  return index


def _JSONifyIndex(index):
  """Return JSON formatted index."""
  # Ordering of these attributes is important for the javascript to parse
  # correctly.
  return json.dumps(
      [(vis['id'], vis['name'],
        vis['spreadsheet_id'], vis['is_public']) for vis in index])


class NetworkX(TemplateView, FormView):
  """Handler for the single-page omni-view."""
  template_name = 'networkx.html'
  form_class = VisForm

  def dispatch(self, request, *args, **kwargs):
    vis_id = int(kwargs['vis_id']) if 'vis_id' in kwargs else None
    # Redirect to the public embed URL if unreachable internally.
    # if vis_id:
      # return HttpResponseRedirect('/vis/%s/embed/' % vis_id)
    return super(NetworkX, self).dispatch(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    """Optional |vis_id| as a matched parameter."""
    context = super(NetworkX, self).get_context_data(**kwargs)
    vis = None
    vis_id = int(kwargs['vis_id']) if 'vis_id' in kwargs else None
    index = _fetchIndex()
    context.update({
        'index': index,
        'vis_count': len(index),
        'hostname': settings.HOSTNAME,
        'json_data': _JSONifyIndex(index)
    })
    if vis_id:
      context['vis_id'] = vis_id
    return context


class NetworkXData(TemplateView):
  """Obtain JSON data for the viss list."""
  def get(self, request, *args, **kwargs):
    index = _fetchIndex()
    return HttpResponse(_JSONifyIndex(index), mimetype='application/json')


class Help(TemplateView):
  template_name = "help.html"

  def get_context_data(self, **kwargs):
    context = super(Help, self).get_context_data(**kwargs)
    context.update({
        "section": "help"
    })
    return context
