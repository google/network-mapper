"""All primary UI view handlers."""

import json
import logging

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View, TemplateView, FormView
from django.views.decorators.csrf import csrf_protect
from google.appengine.api import users
from models import Vis


def _fetchIndex():
  """Obtain list of all visualizations for |user|."""
  user = users.get_current_user()
  if not user:
    return []
  user_id = user.user_id()
  logging.info('Fetching index for user %s', user_id)
  try:
    query = Vis.query(user_id == Vis.user_id)
  except AttributeError:
    query = None
  index = []
  if query:
    index = [vis.to_dict() for vis in query.iter()]
  return index


def _JSONifyIndex(index):
  """Return JSON formatted index."""
  return json.dumps(
      # Attribute order is important for the javascript to parse correctly.
      [(vis['id'], vis['name'],
        vis['spreadsheet_id'], vis['is_public']) for vis in index])


@csrf_protect
def viewUI(request, vis_id=None):
  """Handler which shows the main network mapper UI."""
  index = _fetchIndex()
  return render(request, 'networkx.html', {
      'vis_id': vis_id,
      'index': index,
      'vis_count': len(index),
      'hostname': settings.HOSTNAME,
      'json_data': _JSONifyIndex(index),
  })


def viewVis(request, vis_id):
  """Handler which shows a particular visualization in the UI."""
  # Redirect to the public embed URL if unreachable internally.
  return HttpResponse('viewing id: %s', vis_id)


def getIndexData(request):
  """Handler which returns the visualization index as JSON."""
  index = _fetchIndex()
  return HttpResponse(_JSONifyIndex(index), mimetype='application/json')


def viewHelp(request):
  """Handler which returns the help content."""
  return render(request, 'help.html', {})
