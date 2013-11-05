"""Form-handlers for visualization mutation."""
import logging

from django import forms
from django.forms.widgets import RadioSelect, HiddenInput

from google.appengine.api import users
from google.appengine.ext import deferred

from .models import Graph
from .vis_utils import GenerateNodesThroughSpreadsheet

logger = logging.getLogger(__name__)


class ListFormField(forms.CharField):
  """ Field for use with ndb.StringProperty(repeated=True) """
  def prepare_value(self, value):
    if isinstance(value, list):
      return ','.join(value)
    return value

  def clean(self, value):
    if isinstance(value, (basestring, unicode)):
      return value.split(",")
    return value


class VisForm(forms.Form):
  """Defines the basic form for both creating and updating a graph."""
  name = forms.CharField(required=True, label="Graph Name", max_length=500)
  # spreadsheet_id = forms.CharField(
    # required=False,
    # label="Select your spreadsheet",
    # widget=RadioSelect,
    # max_length=500,
    # help_text="Paste in a valid spreadsheet URL below."
  # )
  spreadsheet_link = forms.URLField(
    required=True,
    label="Spreadsheet Link",
    max_length=500
  )
  is_public = forms.BooleanField(required=False)

  def __init__(self, *args, **kwargs):
    super(VisForm, self).__init__(*args, **kwargs)
    self.obj = None
    graph_id = self.initial.get('graph_id', None)
    if graph_id:
      self.obj = Graph.get_by_id(graph_id)

  def clean_spreadsheet_link(self):
    link = self.cleaned_data["spreadsheet_link"]
    error_msg = "This URL doesn't look like a valid spreadsheet."

    if link == u'':
      return link
    try:
      path, params = link.split("?")
    except ValueError:
      raise forms.ValidationError(error_msg)

    if '#gid=' in params:
      splitted_params = params[:params.find('#gid=')].split("&")
    else:
      splitted_params = params.split("&")

    for param in splitted_params:
      key, value = param.split("=")
      if key == "key":
        return value

    raise forms.ValidationError(error_msg)

  def clean(self):
    cleaned_data = super(VisForm, self).clean()
    spreadsheet_id = cleaned_data.get("spreadsheet_id", None)
    spreadsheet_link = cleaned_data.get("spreadsheet_link", None)

    if not spreadsheet_id and not spreadsheet_link:
      raise forms.ValidationError(
        "You need to select a Google spreadsheet or provide a valid URL.")

    if spreadsheet_link:
      cleaned_data["spreadsheet_id"] = spreadsheet_link

    return cleaned_data

  def save(self):
    """Updates actual data."""
    form_data = self.cleaned_data
    # Determine if this is a creation or an update.
    created = False
    graph = self.obj
    if not graph:
      created = True
      graph = Graph()
      logger.info('New graph created. %s', graph);

    # Fill with data.
    graph.populate(
      name=form_data["name"],
      is_public=form_data["is_public"],
      spreadsheet_id=form_data["spreadsheet_id"]
    )
    if created or not self.obj.user_id:
      graph.user_id = users.get_current_user().user_id()
    graph.put()

    if created:
      # Keep it blocking, because this is an ajax call.
      logger.info(
          'Creating nodes for Graph %s; spreadsheet_id=%s; user_id=%s;',
          graph.key, graph.spreadsheet_id, graph.user_id)
      GenerateNodesThroughSpreadsheet(graph)

    return graph


class DeleteVisForm(forms.Form):
  graph_id = forms.CharField(
    required=True,
    label="",
    max_length=500,
    widget=HiddenInput()
  )

  def __init__(self, *args, **kwargs):
    super(DeleteVisForm, self).__init__(*args, **kwargs)
    self.obj = None
    graph_id = self.initial.get('graph_id', None)
    if graph_id:
      self.obj = Graph.get_by_id(graph_id)
