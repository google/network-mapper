"""Visualization data generation helpers."""

import datetime
import httplib2

from django.core.validators import URLValidator
from google.appengine.ext import ndb
from oauth2client.appengine import StorageByKeyName, CredentialsModel

from clients.conf import CATEGORIES_WORKSHEET_TITLE, NODES_WORKSHEET_TITLE
from clients.spreadsheets import SimpleSpreadsheetsClient
from .vis_conf import MAX_IMPORTANCE, MIN_IMPORTANCE, ERROR_MESSAGES
from .models import Node, ErrorLog, Style


def GenerateData(graph):
  """Generate the entirety of data for a single graph."""
  from .models import Node
  all_nodes = Node.query(Node.graph == graph.key, )
  all_categories = all_nodes.filter(Node.is_category == True)
  nodes = all_nodes.filter(Node.is_category == False)
  categories_position = {}
  graph_data = {'nodes': [], 'links': []}

  # First determine categories to include.
  for index, category in enumerate(all_categories):
    graph_data['nodes'].append({
        'name': category.name,
        'is_category': category.is_category,
        'node_style': category.node_style or '',
        'label_style': category.label_style or '',
        'group': index + 1,
        'importance': 0
    })
    categories_position[category.key.id()] = index

  start = len(graph_data['nodes'])
  for index, node in enumerate(nodes):
    node_data = { 'name': node.name }
    node_data['context_url'] = node.context_url if node.context_url else ''
    node_data['short_description'] = node.short_description if node.short_description else ''
    node_data['long_description'] = node.long_description if node.long_description else ''
    node_data['credit'] = node.credit or ''
    node_data['youtube_id'] = node.context_youtube_id
    node_data['node_style'] = node.node_style or ''
    node_data['label_style'] = node.label_style or ''
    node_data['importance'] = node.importance or 1

    # if node_data['credit'] and node_data['credit'].startswith("http://"):
    #   node_data['credit'] = '<a href="%(link)s" target="_blank">%(link)s</a>' % {"link": node_data['credit']}

    graph_data['nodes'].append(node_data)
    for c_index, category_key in enumerate(node.categories):
      graph_data['links'].append({
        'source': start + index,
        'target': categories_position[category_key.id()]
      })
      if c_index == 0:
        node_data['group'] = categories_position[category_key.id()] + 1

  return graph_data


def _KeysToDelete(model_class, ancestor_key):
  query = model_class.query(ancestor=ancestor_key)
  return [key for key in query.iter(keys_only=True)] 


def GenerateNodesThroughSpreadsheet(graph):
  """Parse spreadsheet data into nodes from graph."""
  storage = StorageByKeyName(CredentialsModel, graph.user_id, 'credentials')
  credentials = storage.get()

  # Ensure this is good.
  if credentials.access_token_expired:
    http = httplib2.Http()
    credentials.refresh(http)
    storage.put(credentials)

  # Prepare client and fetch data from a google spreadsheet.
  client = SimpleSpreadsheetsClient(credentials)
  fetched_categories = client.GetCategories(graph.spreadsheet_id)
  fetched_nodes = client.GetNodes(graph.spreadsheet_id)
  fetched_data_css = client.GetDataCss(graph.spreadsheet_id)
  fetched_generic_css = client.GetGenericCss(graph.spreadsheet_id)

  categories = {}
  error_log_list = []

  @ndb.transactional()
  def _transaction():
    # First, delete existing nodes, categories, and logs.
    keys_to_delete = []
    keys_to_delete.extend(_KeysToDelete(Node, graph.key))
    keys_to_delete.extend(_KeysToDelete(ErrorLog, graph.key))
    keys_to_delete.extend(_KeysToDelete(Style, graph.key))
    ndb.delete_multi(keys_to_delete)

    # Parse node categories.
    for f_category in fetched_categories:
      category = Node(parent=graph.key)
      category.populate(
        is_category=True,
        name=f_category["name"],
        graph=graph.key,
        node_style=f_category["node_style"],
        label_style=f_category["label_style"],
      )
      category.put()
      categories[f_category["name"]] = category

    if categories:
      for (counter, f_node) in enumerate(fetched_nodes):
        copied_node = f_node.copy()
        error_log = _ValidateNode(copied_node, categories)
        # Remember each valid Node.
        if not error_log:
          node = Node(parent=graph.key)
          node.populate(
            graph=graph.key,
            name=copied_node["name"],
            short_description=copied_node["short_description"],
            long_description=copied_node["long_description"],
            context_url=copied_node["context_url"],
            importance=int(copied_node["importance"]),
            credit=copied_node["credit"],
            node_style=copied_node["node_style"],
            label_style=copied_node["label_style"],
          )
          for node_category in _ListCategories(copied_node):
            node.categories.append(categories[node_category].key)
          node.put()
        else:
          error_log_list.append({
            'node': {
              # spreadsheets row starts from 1 and must count the removed header
              'row': counter + 2,
              'errors': error_log,
            }
          })

      styles = []
      # Parse simple custom styles, then combine with optional generic styling.
      for classname, attributes in fetched_data_css.iteritems():
        styles.append(
          '.%s { %s }' % (classname, ' '.join(attributes))
        )
      style = Style(parent=graph.key)
      style.populate(
          graph=graph.key,
          styles='\n'.join(styles) + '\n' + fetched_generic_css,
      )
      style.put()

      graph.last_updated = datetime.datetime.now()
      graph.put()

    else:  # No categories.
      error_log_list.append({
        'graph': {
          'errors': [
              'The spreadsheet selected must contain 2 worksheets named \'{0:s}\''
              'and \'{1:s}\'. \'{0:s}\' must contain at least one category'.format(
                CATEGORIES_WORKSHEET_TITLE, NODES_WORKSHEET_TITLE), ],
        }
      })

    if error_log_list:
      error_log = ErrorLog(parent=graph.key)
      error_log.populate(
        graph=graph.key,
        json_log=error_log_list
      )
      error_log.put()

  _transaction()


def _ListCategories(node):
  """Returns the categories within a fetched (non-ndb) node."""
  if node['categories']:
    return node['categories'].replace(' ', '').split(',')


def _ValidateNode(node, all_categories=None):
  """
  Validates a single node.
  Returns an error log.
  """
  error_log = {}

  if not node['name']:
    error_log['name'] = [ERROR_MESSAGES['required'], ]
  url = node['context_url']

  if url:
    try:
      URLValidator(url)
    except:
      error_log['Context Url'] = [ERROR_MESSAGES['invalid_url'], ]

  importance = node["importance"]
  if importance:
    try:
      importance = int(importance)
    except ValueError:
      error_log['Importance'] = [ERROR_MESSAGES['invalid_integer'], ]
    else:
      if not (MIN_IMPORTANCE <= importance <= MAX_IMPORTANCE):
        error_log['Importance'] = [
          ERROR_MESSAGES['min_value'] % {'limit_value': MIN_IMPORTANCE},
          ERROR_MESSAGES['max_value'] % {'limit_value': MAX_IMPORTANCE},
        ]
  else:
    error_log['Importance'] = [ERROR_MESSAGES['required'], ]

  node_categories = _ListCategories(node)
  if not node_categories:
    error_log['Categories'] = [ERROR_MESSAGES['required'], ]
  else:
    error_log['Categories'] = []
    for category in node_categories:
      if category not in all_categories:
        error_log['Categories'].append(
            ERROR_MESSAGES['invalid_choice'] % {'value': category})
    if not error_log['Categories']:
      del error_log['Categories']

  return error_log
