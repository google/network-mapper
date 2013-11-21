"""All visualization-specific view handlers."""

import json
import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.datastructures import SortedDict
from django.views.generic import View, TemplateView, FormView
from django.views.decorators.http import require_GET, require_POST

from django.views.generic.base import TemplateResponseMixin
from google.appengine.ext import ndb
from google.appengine.api import users
from auth.utils import GetCurrentCredentials
from auth.mixins import OAuth2RequiredMixin
from clients.drive import SimpleDriveClient

from .models import Vis, Node, ErrorLog, Style
import vis_utils as VisUtils


def authenticate(request, vis):
  """Authenticates |vis|.

  Ensure |vis| is either public, or has appropriate credentials for user.

  Returns |vis| if authenticated. Raises PermissionDenied otherwise.
  """
  if not vis.is_public:
    user = None
    if request.session.get('credentials', None):
      user = users.get_current_user()
    if not user:
      raise PermissionDenied
  # TODO: Ensure the id contained in request matches vis.
  return vis


def getVis(vis_id):
  """Fetches a Vis entity. Not authenticated."""
  vis_id = int(vis_id)  # Casting to int is required or ndb lookup fails.
  if not vis_id:
    raise Http404
  vis = Vis.get_by_id(vis_id)
  if not vis:
    raise Http404
  return vis


def getJSONData(request, vis_id):
  """Handler which returns JSON data for a Vis."""
  return HttpResponse(
      json.dumps(VisUtils.generateData(authenticate(request, getVis(vis_id)))),
      content_type="application/json")


def createVis(request):
  """Handler which creates a new visualization."""
  vis = VisUtils.createVisualization(request.POST)
  return HttpResponse('created. id: %s', vis)


def viewVis(request, vis_id):
  """Handler which renders the basic standalone visualization."""
  vis = authenticate(request, getVis(vis_id))
  styles = ''.join(map(lambda s: s.styles,
               Style.query(Style.vis == vis.key)))
  return render(request, 'vis.html', {
      'vis_id': vis_id,
      'vis': vis,
      'vis_style': styles
      })


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


def deleteVis(request, vis_id):
  """Handler which deletes a visualization from the index."""
  # TODO: indicate that it doesn't delete the google doc.
  VisUtils.deleteVisualization(authenticate(request, getVis(vis_id)))
  return HttpResponse('deleted.')


def getLog(request, vis_id):
  """Handler which returns the log data for a visualization."""
  vis = authenticate(request, getVis(vis_id))
  logging.info(ErrorLog.__dict__)
  latest_log = ErrorLog.query(ErrorLog.vis == vis.key).order(-ErrorLog.modified).get()
  if latest_log and latest_log.modified >= vis.modified:
    error_log = latest_log.json_log
  # log = ErrorLog.get_by_id(vis)
  return render(request, 'log.html', {
      'error_log': error_log })


# TODO(keroserene): Make this list only "valid" spreadsheets, maybe, if we even
# care about this functionality anymore.
class SpreadsheetList(View):
  """Returns list of all spreadsheets."""
  def get(self, request, *args, **kwargs):
    credentials = GetCurrentCredentials()
    client = SimpleDriveClient(credentials)
    spreadsheets = client.get_spreadsheet_list()
    spreadsheet_id = None

    referral_url = request.META.get('HTTP_REFERER', '').strip('/')
    splitted_url = referral_url.split('/')
    if splitted_url[-1] == 'update':
      graph = Vis.get_by_id(int(splitted_url[-2]))
      spreadsheet_id = graph.spreadsheet_id

    return render(
      request, 'graph/options_spreadsheet_form.html', {
          'spreadsheets': spreadsheets,
          'current_spreadsheet_id': spreadsheet_id})


# class NodeDetail(_VisBaseView):
  # """JSON response for a single node. Detail popups should be AJAX'd."""
  # def get(self, request, *args, **kwargs):
    # if request.is_ajax():
      # message = {}
      # node = ndb.Key(
          # 'Vis', int(kwargs['vis_id']),
          # 'Node', int(kwargs['node_id'])).get()
      # if not node:
        # raise Http404
      # else:
        # message['name'] = node.name
        # message['short_description'] = node.short_description
        # message['long_description'] = node.long_description
        # message['context_url'] = node.context_url
        # message['defection_url'] = node.defection_url
      # myjson = json.dumps(message)
      # return HttpResponse(myjson, mimetype='application/json')
    # else:
      # raise Http404

