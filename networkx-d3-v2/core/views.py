import json
import logging
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.generic import View, TemplateView, FormView
from google.appengine.api import users

from graph.models import Graph
from graph.forms import GraphForm


def FetchGraphs():
  user = users.get_current_user()
  try:
    graphs_query = Graph.query(Graph.user_id == user.user_id())
  except AttributeError:
    []
  return graphs_query


def _JSONify(graphs_query):
  graphs = [graph.to_dict() for graph in graphs_query.iter()]
  graphs = [(graph['graph_id'],
             graph['name'],
             graph['spreadsheet_id'],
             graph['is_public']) for graph in graphs]
  return json.dumps(graphs)


class NetworkX(TemplateView, FormView):
  """Handler for the single-page omni-view."""
  template_name = "networkx.html"
  form_class = GraphForm

  def dispatch(self, request, *args, **kwargs):
    graph_id = int(kwargs['graph_id']) if 'graph_id' in kwargs else None
    # Redirect to the public embed URL if unreachable internally.
    # if graph_id:
      # return HttpResponseRedirect('/graph/%s/embed/' % graph_id)
    return super(NetworkX, self).dispatch(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    """Optional |graph_id| as a matched parameter."""
    context = super(NetworkX, self).get_context_data(**kwargs)
    graph = None
    graph_id = int(kwargs['graph_id']) if 'graph_id' in kwargs else None

    graphs_query = FetchGraphs()
    graphs = [graph for graph in graphs_query.iter()]
    if graph_id:
      graph = Graph.get_by_id(graph_id)
      if graph not in graphs:
        raise Http404

    context.update({
        'form': GraphForm,
        'graphs': graphs,
        'graphs_count': len(graphs) if graphs else 0,
        'section': 'homepage',
        'hostname': settings.HOSTNAME,
        'json_data': _JSONify(graphs_query)
    })

    if graph_id:
      context.update({
          'graph_id': graph_id,
          'graph': graph})

    return context


class NetworkXData(TemplateView):
  """Obtain JSON data for the graphs list."""
  def get(self, request, *args, **kwargs):
    graphs_query = FetchGraphs()
    return HttpResponse(_JSONify(graphs_query), mimetype='application/json')


class Help(TemplateView):
  template_name = "help.html"

  def get_context_data(self, **kwargs):
    context = super(Help, self).get_context_data(**kwargs)
    context.update({
        "section": "help"
    })
    return context
