"""All visualization-specific view handlers."""

import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from google.appengine.api import users

from .models import Vis, ErrorLog, Style
import vis_utils as VisUtils


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


@require_GET
def getIndexData(request):
  """Handler which returns the visualization index as JSON."""
  index = _fetchIndex()
  return HttpResponse(_JSONifyIndex(index), mimetype='application/json')


@require_GET
def viewHelp(request):
  """Handler which returns the help content."""
  return render(request, 'help.html', {})


def getVis(vis_id):
  """Fetch a Vis entity. Does not authenticate."""
  if not vis_id:
    raise Http404
  vis = Vis.get_by_id(int(vis_id))  # Cast to int required or ndb lookup fails.
  if not vis:
    raise Http404
  return vis


def authenticate(request, vis):
  """Authenticate |request| for |vis|.
  Returns: |vis| if it's public, or belongs to the current user.
  Raises: PermissionDenied otherwise.
  """
  if not vis.is_public:
    user = None
    if request.session.get('credentials', None):
      user = users.get_current_user()
    if not user:
      raise PermissionDenied
  # TODO: Ensure the id contained in request matches vis.
  return vis


@require_GET
def getJSONData(request, vis_id):
  """Handler which returns JSON data for a Vis."""
  return HttpResponse(
      json.dumps(VisUtils.generateData(authenticate(request, getVis(vis_id)))),
      content_type="application/json")


@require_POST
def createVis(request):
  """Handler which creates a new visualization."""
  vis = VisUtils.createVisualization(request.POST)
  return HttpResponse('created. id: %s', vis)


@require_GET
def viewVis(request, vis_id):
  """Handler which renders the basic standalone visualization."""
  vis = authenticate(request, getVis(vis_id))
  styles = ''.join(
      map(lambda s: s.styles, Style.query(Style.vis == vis.key)))
  return render(request, 'vis.html', {
      'vis_id': vis_id,
      'vis': vis,
      'vis_style': styles
      })


@require_POST
def updateVis(request, vis_id):
  """Handler which updates a visualization's meta-data."""
  VisUtils.saveVisualization(
      authenticate(request, getVis(vis_id)),
      data=request.POST)
  return HttpResponse('updated.')


def refreshVis(request, vis_id):
  """Handler which refreshes visualization's data from spreadsheet."""
  VisUtils.generateFromSpreadsheet(
      authenticate(request, getVis(vis_id)))
  return HttpResponse('refreshed.')


@require_POST
def deleteVis(request, vis_id):
  """Handler which deletes a visualization from the index."""
  # TODO: indicate that it doesn't delete the google doc.
  VisUtils.deleteVisualization(authenticate(request, getVis(vis_id)))
  return HttpResponse('deleted.')


@require_GET
def getLog(request, vis_id):
  """Handler which returns the log data for a visualization."""
  vis = authenticate(request, getVis(vis_id))
  logging.info(ErrorLog.__dict__)
  latest_log = ErrorLog.query(ErrorLog.vis == vis.key).order(-ErrorLog.modified).get()
  if latest_log and latest_log.modified >= vis.modified:
    error_log = latest_log.json_log
  return render(request, 'log.html', {
      'error_log': error_log })


@csrf_protect
def thumbs(request, vis_id):
  """Handler for interacting with visualization thumbnails."""
  logging.info(request.method)
  if 'POST' == request.method:
    img = request.POST.get('thumb')
    VisUtils.saveThumbnail(authenticate(request, getVis(vis_id)), img)
    return HttpResponse('updated thumbnail for ' + vis_id)
  elif 'GET' == request.method:
    logging.info('getting a thumbnail.')
    return HttpResponse(authenticate(request, getVis(vis_id)).thumbnail)


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
      [(vis['id'],
        vis['name'],
        vis['spreadsheet_id'],
        vis['is_public'],
        vis['thumbnail']) for vis in index])
