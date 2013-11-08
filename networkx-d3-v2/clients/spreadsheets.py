"""Interaction helpers for Google Spreadsheets."""

import re
import logging

from collections import defaultdict

from gdata.gauth import AuthSubToken
from gdata.spreadsheets.client import SpreadsheetsClient
from .conf import (
  CATEGORIES_WORKSHEET_TITLE,
  NODES_WORKSHEET_TITLE,
  STYLES_WORKSHEET_TITLE,
  HASH_SPREADSHEET_NODES_TABLE_TO_JSON,
  HASH_SPREADSHEET_CATEGORIES_TABLE_TO_JSON)


class SimpleSpreadsheetsClient(SpreadsheetsClient):
  """Client for interacting with a spreadsheet."""

  def __init__(self, credentials, *args, **kwargs):
    """
    We expect some OAuth2 credentials that allow us to authorize the user,
    so we assume that the access_token is valid. Is the caller's
    responsability to refresh the tokens if needed.
    """
    self.auth_token = AuthSubToken(credentials.access_token)
    super(SimpleSpreadsheetsClient, self).__init__(*args, **kwargs)

  def GetCustomWorksheets(self, spreadsheet_id):
    fetched_worksheets = self.get_worksheets(
      spreadsheet_id,
      auth_token=self.auth_token)
    worksheets = {
      'categories': None,
      'nodes': None,
      'styles': None,
    }
    for ws in fetched_worksheets.entry:
      title = ws.title.text
      if CATEGORIES_WORKSHEET_TITLE == title:
        worksheets['categories'] = ws
      elif NODES_WORKSHEET_TITLE == title:
        worksheets['nodes'] = ws
      elif STYLES_WORKSHEET_TITLE == title:
        worksheets['styles'] = ws
    return worksheets

  def _extract_rows(self, spreadsheet_id, worksheet, hasher):
    rows = {}
    cells = self.get_cells(
      spreadsheet_id,
      worksheet.get_worksheet_id()
    )
    for cell in cells.entry:
      # the return value for cell.id.text is something like
      # 'https://spreadsheets.google.com/feeds/cells/<spreadsheet_id>/<worksheet_id>/R1C1'
      cell_id = cell.id.text.split('/')[-1]
      content = cell.content.text
      row, column = map(
        int,
        cell_id.replace('R', '').replace('C', ',').split(','))

      if not row in rows:
        rows[row] = dict([(v, None) for v in hasher.values()])

      if column in hasher:
        rows[row][hasher[column]] = str.strip(content) if content else None

    if rows:
      del rows[1]
    return rows.values()

  def GetCategories(self, spreadsheet_id):
    categories_ws = self.GetCustomWorksheets(spreadsheet_id)['categories']
    if categories_ws:
      return self._extract_rows(
        spreadsheet_id,
        categories_ws,
        HASH_SPREADSHEET_CATEGORIES_TABLE_TO_JSON
      )

    return []

  def GetNodes(self, spreadsheet_id):
    nodes_ws = self.GetCustomWorksheets(spreadsheet_id)['nodes']
    if nodes_ws:
      return self._extract_rows(
        spreadsheet_id,
        nodes_ws,
        HASH_SPREADSHEET_NODES_TABLE_TO_JSON
      )

    return []

  def GetDataCss(self, spreadsheet_id):
    """Extract simple, data-relevant CSS styling from the spreadsheet.

    @Returns:
      Dict of CSS classname ->attributes
    """
    styles_ws = self.GetCustomWorksheets(spreadsheet_id)['styles']
    styles = defaultdict(list)
    if styles_ws:
      cells = self.get_cells(
        spreadsheet_id,
        styles_ws.get_worksheet_id(),
      )
      for cell in cells.entry:
        cell_id = cell.id.text.split('/')[-1]
        content = cell.content.text
        row, column = map(
          int,
          cell_id.replace('R', '').replace('C', ',').split(',')
        )
        if column == 1:
          if row == 1:
            class_column_heading = content
          # CSS class name.
          content = re.match(r'\.?(.*)', content).group(1)
          class_styles = styles[content]
        elif column == 2:
          # CSS value.
          class_styles.append(content)

    del styles[class_column_heading]

    return dict(styles)

  def GetGenericCss(self, spreadsheet_id):
    """Extract the generic CSS textblocks from the spreadsheet.

    This is distinct from get_styles in that this is for the fully customizable
    generic CSS code in a single cell from the spreadsheet, while get_styles is
    a table of simple class names and attributes.

    @Returns:
      Single string containing the custom css, or the empty string.
    """

    css_ws = self.GetCustomWorksheets(spreadsheet_id)['styles']
    if css_ws:
      # Assume the custom CSS is in cell D2
      # TODO(keroserene): Make this more sensible.
      css_cell = self.get_cell(
          spreadsheet_id, css_ws.get_worksheet_id(), 2, 4)
      return css_cell.content.text or ''
