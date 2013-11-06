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

from .forms import VisForm, DeleteVisForm
from .vis_utils import GenerateData, GenerateNodesThroughSpreadsheet
from .models import Graph, Node, ErrorLog, Style


class VisBaseMixin(object):
  """Authenticated query for a single graph."""
  def dispatch(self, request, *args, **kwargs):
    self.vis_id = kwargs.get('vis_id')
    if self.vis_id:
      self.vis = Graph.get_by_id(int(kwargs['vis_id']))
      if not self.vis:
        raise Http404
      if not self.vis.is_public:
        user = None
        if request.session.get('credentials', None):
          user = users.get_current_user()
        if not user:
          logging.info('Visualization %s is not public. Denied.' % vis_id)
          raise PermissionDenied
      return super(VisBaseMixin, self).dispatch(request, *args, **kwargs)
    raise Http404


class _VisBaseView(VisBaseMixin, View):
  """Base view providing only the id and main data."""
  def get_context_data(self, *args, **kwargs):
    ctx = super(_VisBaseView, self).get_context_data(*args, **kwargs)
    ctx.update({
        'vis_id': self.vis_id,
        'vis': self.vis
    })
    return ctx


class VisView(_VisBaseView, TemplateView):
  """Standalone visualization view. Used as the basis for UI view & edits."""
  template_name = 'vis.html'

  def get_context_data(self, **kwargs):
    ctx = {}
    nodes = Node.query(Node.is_category == False)
    # make a list of the categories & counts
    category_list = Node.query(
        Node.is_category == True,
        Node.graph == self.vis.key)
    nodes_by_category = SortedDict()
    for category in category_list:
      # search for nodes who are tagged as part of this category.
      number = nodes.filter(Node.categories.IN([category.key])).count(limit=None)
      nodes_by_category.update({category.name: number})
    nodes_by_category.update({ 'total': nodes.count(limit=None) })

    styles = []
    vis_style = Style.query(Style.graph == self.vis.key)
    for style in vis_style:
      styles.append(style.styles)

    # TODO(keroserene): Make this not defection-tracker dependent.
    ctx.update({
        'defections_by_category': nodes_by_category,
        'category_list': category_list,
        'vis_style': ''.join(styles),
    })
    return ctx


def GetGraph(vis_id):
  """Authenticated attempt to obtain graph by id."""
  if not vis_id:
    raise Http404
  graph = Graph.get_by_id(vis_id)
  if not graph:
    raise Http404
  if not graph.is_public:
    user = None
    if request.session.get('credentials', None):
      user = users.get_current_user()
    if not user:
      raise PermissionDenied
  return vis_id


class Data(_VisBaseView):
  """Obtain pure JSON data for a single graph."""
  def get(self, request, *args, **kwargs):
    return HttpResponse(
        json.dumps(GenerateData(self.vis)),
        content_type="application/json")


class GraphStandaloneView(_VisBaseView, TemplateView):
  template_name = "graph/graph_standalone.html"


class NodeDetail(_VisBaseView):
  """JSON response for a single node. Detail popups should be AJAX'd."""
  def get(self, request, *args, **kwargs):
    if request.is_ajax():
      message = {}
      node = ndb.Key(
          'Graph', int(kwargs['vis_id']),
          'Node', int(kwargs['node_id'])).get()
      if not node:
        raise Http404
      else:
        message['name'] = node.name
        message['short_description'] = node.short_description
        message['long_description'] = node.long_description
        message['context_url'] = node.context_url
        message['defection_url'] = node.defection_url
      myjson = json.dumps(message)
      return HttpResponse(myjson, mimetype='application/json')
    else:
      raise Http404


class VisFormMixin(object):
  """Base for a form handler."""
  template_name = 'graph_form.html'
  form_class = VisForm

  def form_valid(self, form):
    form.save()  # Causes a save OR a create.
    return HttpResponse('success')  # No actual response URL.


class VisFetchingMixin(object):
  """Authenticates the graph fetch."""
  def dispatch(self, request, *args, **kwargs):
    self.vis_id = int(kwargs.get('vis_id'))
    if self.vis_id:
      self.vis = Graph.get_by_id(self.vis_id)
      if not self.vis:
        raise Http404
      user = users.get_current_user()
      if user.user_id() != self.vis.user_id:
        raise PermissionDenied
      return super(VisFetchingMixin, self).dispatch(request, *args, **kwargs)
    raise Http404

  def get_context_data(self, *args, **kwargs):
    context = super(VisFetchingMixin, self).get_context_data(*args, **kwargs)
    context.update({
      'vis_id': self.vis_id,
      'vis': self.vis
    })
    return context


class CreateVis(OAuth2RequiredMixin, VisFormMixin, FormView):
  def dispatch(self, *args, **kwargs):
    self.user = users.get_current_user()
    return super(CreateVis, self).dispatch(*args, **kwargs)


class UpdateVis(OAuth2RequiredMixin, VisFetchingMixin, VisFormMixin, FormView):
  def get_initial(self):
    return self.vis.to_dict()


class DeleteVis(OAuth2RequiredMixin, VisFetchingMixin, FormView):
  template_name = 'confirm_delete.html'
  form_class = DeleteVisForm
  # TODO: indicate that it doesn't delete the google doc.

  def get_initial(self):
    return self.vis.to_dict()

  def form_valid(self, form):
    """Validate the form and delete the visualization."""
    logging.info('Deleting %s', self.vis.key)
    form.delete(self.vis)
    messages.info(self.request, 'Vis deleted')
    return HttpResponse('delete.')

  def get_context_data(self, *args, **kwargs):
    ctx = super(DeleteVis, self).get_context_data(*args, **kwargs)
    ctx.update({
      'vis_id': self.vis_id,
      'vis': self.vis
    })
    return ctx


class RefreshVis(OAuth2RequiredMixin, _VisBaseView):

  def get(self, request, *args, **kwargs):
    GenerateNodesThroughSpreadsheet(self.vis)
    messages.info(
        request,
        'Requested latest data for \'%s\'.' % self.vis.name +
        'This may take a few minutes to complete.')
    return HttpResponse('Refreshed spreadsheet data for %s.' % self.vis.name)


class ErrorLog(OAuth2RequiredMixin, VisBaseMixin,
               VisFetchingMixin, TemplateView):
  template_name = 'graph/graph_error_log.html'

  def get_context_data(self, **kwargs):
    context = super(ErrorLog, self).get_context_data(**kwargs)
    latest_log = ErrorLog.query(ErrorLog.graph == self.vis.key).order(-ErrorLog.modified).get()
    if latest_log and latest_log.modified >= self.vis.modified:
      error_log = latest_log.json_log
    else:
      error_log = None
    context.update({
        'page_title': 'Graph Log',
        'graph': self.vis,
        'error_log': error_log
    })
    return context


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
      graph = Graph.get_by_id(int(splitted_url[-2]))
      spreadsheet_id = graph.spreadsheet_id

    return render(
      request, 'graph/options_spreadsheet_form.html', {
          'spreadsheets': spreadsheets,
          'current_spreadsheet_id': spreadsheet_id})

