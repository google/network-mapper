"""Django-based models for Visualization Viss."""

import logging

from google.appengine.ext import ndb
from urlparse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class BaseModel(ndb.Model):
  """Base model with only creation and modification timestamps."""
  created = ndb.DateTimeProperty(auto_now_add=True)
  modified = ndb.DateTimeProperty(auto_now=True)


class Vis(BaseModel):
  """Basic metadata required for a single visualization."""
  name = ndb.StringProperty()
  user_id = ndb.StringProperty(required=True, verbose_name='User ID')
  spreadsheet_id = ndb.StringProperty(required=True,
                                      verbose_name='Spreadsheet ID')
  is_public = ndb.BooleanProperty(default=False)
  last_updated = ndb.DateTimeProperty(auto_now_add=True)

  def __unicode__(self):
    return self.name

  def to_dict(self):
    data = super(Vis, self).to_dict()
    data.update({ 'id': self.key.id() })
    return data


class ErrorLog(BaseModel):
  vis = ndb.KeyProperty(Vis, required=True)
  json_log = ndb.JsonProperty(repeated=True)

  def __unicode__(self):
    return self.json_log


class Node(BaseModel):
  """Data for a single node in a visualization."""
  is_category = ndb.BooleanProperty(default=False)
  name = ndb.StringProperty(required=True)
  vis = ndb.KeyProperty(Vis, required=True)
  short_description = ndb.TextProperty(verbose_name='Short Description')
  long_description = ndb.TextProperty(verbose_name='Long Description')
  context_url = ndb.StringProperty(verbose_name='Context URL')
  credit = ndb.StringProperty(verbose_name='Credit')
  importance = ndb.IntegerProperty()
  categories = ndb.KeyProperty('Node', repeated=True)
  node_style = ndb.StringProperty()
  label_style = ndb.StringProperty()

  @property
  def context_youtube_id(self):
    url = None
    youtube_id = None
    if self.context_url:
      url = urlparse(self.context_url)
    if url and url.netloc == "www.youtube.com":
      url_querystring = parse_qs(url.query)
      youtube_id = url_querystring.get("v", None)
    if youtube_id:
      return youtube_id[0]
    if self.context_url:
      url = urlparse(self.context_url)
    if url and url.netloc == "www.youtube.com":
      url_querystring = parse_qs(url.query)
      youtube_id = url_querystring.get("v", None)
    if youtube_id:
      return youtube_id[0]
    else:
      return None

  def __unicode__(self):
    return self.name


class Style(BaseModel):
  vis = ndb.KeyProperty(Vis, required=True)
  styles = ndb.TextProperty()
  # generic_css = ndb.TextProperty()
