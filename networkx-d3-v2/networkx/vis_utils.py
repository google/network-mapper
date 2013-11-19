"""Visualization data generation helpers."""

import datetime
import httplib2
import logging
import thread

from django.core.validators import URLValidator
from google.appengine.ext import ndb
from google.appengine.api import users
from oauth2client.appengine import StorageByKeyName, CredentialsModel

from clients.conf import CATEGORIES_WORKSHEET_TITLE, NODES_WORKSHEET_TITLE
from clients.spreadsheets import SimpleSpreadsheetsClient
from .vis_conf import MAX_IMPORTANCE, MIN_IMPORTANCE, ERROR_MESSAGES
from .models import Vis, Node, ErrorLog, Style


def acquireLatestCredentials(user_id):
  """Returns credentials, and refreshes them if necessary."""
  storage = StorageByKeyName(CredentialsModel, user_id, 'credentials')
  credentials = storage.get()
  if credentials.access_token_expired:
    logging.info('Credentials expired. Attempting to refresh...')
    credentials.refresh(httplib2.Http())
    storage.put(credentials)
    logging.info('Successfully refreshed access token!')
  return credentials


def generateData(vis):
  """generate the entirety of data for a single vis."""
  from .models import Node
  all_nodes = Node.query(Node.vis == vis.key,)
  all_categories = all_nodes.filter(Node.is_category == True)
  nodes = all_nodes.filter(Node.is_category == False)

  vis_data = {'nodes': [], 'links': []}
  categories_position = {}
  # First determine categories to include.
  for index, category in enumerate(all_categories):
    vis_data['nodes'].append({
        'name': category.name,
        'is_category': category.is_category,
        'node_style': category.node_style or '',
        'label_style': category.label_style or '',
        'group': index + 1,
        'importance': 0
    })
    categories_position[category.key.id()] = index

  start = len(vis_data['nodes'])
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

    vis_data['nodes'].append(node_data)
    for c_index, category_key in enumerate(node.categories):
      vis_data['links'].append({
        'source': start + index,
        'target': categories_position[category_key.id()]
      })
      if 0 == c_index:
        node_data['group'] = categories_position[category_key.id()] + 1

  return vis_data


def _KeysToDelete(model_class, ancestor_key):
  query = model_class.query(ancestor=ancestor_key)
  return [key for key in query.iter(keys_only=True)]


def generateNodesFromSpreadsheet(vis):
  """Parse spreadsheet data into nodes from vis."""
  logging.info('Generating data using spreadsheet id: %s', vis.spreadsheet_id)

  credentials = acquireLatestCredentials(vis.user_id)
  # Prepare client and fetch data from a google spreadsheet.
  client = SimpleSpreadsheetsClient(credentials)
  fetched_categories = client.GetCategories(vis.spreadsheet_id)
  fetched_nodes = client.GetNodes(vis.spreadsheet_id)
  fetched_data_css = client.GetDataCss(vis.spreadsheet_id)
  fetched_generic_css = client.GetGenericCss(vis.spreadsheet_id)

  categories = {}
  error_log_list = []

  @ndb.transactional()
  def _transaction():
    # First, delete existing nodes, categories, and logs.
    keys_to_delete = []
    keys_to_delete.extend(_KeysToDelete(Node, vis.key))
    keys_to_delete.extend(_KeysToDelete(ErrorLog, vis.key))
    keys_to_delete.extend(_KeysToDelete(Style, vis.key))
    ndb.delete_multi(keys_to_delete)

    # Parse node categories.
    for f_category in fetched_categories:
      category = Node(parent=vis.key)
      category.populate(
        is_category=True,
        name=f_category['name'],
        vis=vis.key,
        node_style=f_category['node_style'],
        label_style=f_category['label_style'],
      )
      category.put()
      categories[f_category['name']] = category

    if categories:
      for (counter, f_node) in enumerate(fetched_nodes):
        copied_node = f_node.copy()
        error_log = _ValidateNode(copied_node, categories)
        # Remember each valid Node.
        if not error_log:
          node = Node(parent=vis.key)
          node.populate(
            vis=vis.key,
            name=copied_node['name'],
            short_description=copied_node['short_description'],
            long_description=copied_node['long_description'],
            context_url=copied_node['context_url'],
            importance=int(copied_node['importance']),
            credit=copied_node['credit'],
            node_style=copied_node['node_style'],
            label_style=copied_node['label_style'],
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
      style = Style(parent=vis.key)
      style.populate(
          vis=vis.key,
          styles='\n'.join(styles) + '\n' + fetched_generic_css,
      )
      style.put()

      vis.last_updated = datetime.datetime.now()
      vis.put()

    else:  # No categories.
      error_log_list.append({
        'vis': {
          'errors': [
              'The spreadsheet selected must contain 2 worksheets named \'{0:s}\''
              'and \'{1:s}\'. \'{0:s}\' must contain at least one category'.format(
                CATEGORIES_WORKSHEET_TITLE, NODES_WORKSHEET_TITLE), ],
        }
      })

    if error_log_list:
      error_log = ErrorLog(parent=vis.key)
      error_log.populate(
        vis=vis.key,
        json_log=error_log_list
      )
      error_log.put()

  _transaction()


def extractIdFromUrl(url):
  """Parse |url| hoping to get a spreadsheet id."""
  if not url:
    return 0
  return url.split('?key=')[1].split('&')[0] #.split('#')[0]


def createVisualization(data):
  """Creates and returns a new visualization using POST |data|."""
  logging.info('Creating new visualization...')
  newVis = Vis()
  # newVis.user_id = users.get_current_user().user_id()
  logging.info('user id: %s', newVis.user_id)
  saveVisualization(newVis, data)  # Will .put() into ndb.
  logging.info(
      'Creating nodes for vis %s; spreadsheet_id=%s; user_id=%s;',
      newVis.key, newVis.spreadsheet_id, newVis.user_id)
  generateNodesFromSpreadsheet(newVis)
  logging.info('New vis created. %s', newVis);
  newVis.put()
  return newVis


def saveVisualization(vis, data):
  """Updates |vis| with |data| and saves to ndb."""
  spreadsheet_id = extractIdFromUrl(data.get('spreadsheet_link'))
  vis.populate(
    name = data.get('name'),
    is_public = data.get('is_public', False),
    # TODO: Make spreadsheet_id vs. spreadsheet_link actually consistent...
    spreadsheet_id = spreadsheet_id
  )
  if not vis.user_id:
    # Ensure the visualization has the correct user ID.
    # Assumes get_current_user() is authenticated.
    vis.user_id = users.get_current_user().user_id()
  vis.put()
  logging.info('saving %s', vis)


def deleteVisualization(vis):
  """Deletes |vis| from ndb. Assumes authentication has occured."""
  nodes = Node.query(Node.vis == vis.key)
  vis.key.delete()  # Disappears from the index at this point.
  # Delete the rest of the nodes in a separate thread.
  thread.start_new_thread(_deleteNodes, (nodes,))
  logging.info('Deleted %s', vis.key)


def _deleteNodes(nodes): map(lambda n: n.key.delete(), nodes)



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
