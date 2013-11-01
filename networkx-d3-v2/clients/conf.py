"""Required entries for spreadsheet data."""

from django.conf import settings

CATEGORIES_WORKSHEET_TITLE = getattr(settings, 'CATEGORIES_WORKSHEET_TITLE', 'CATEGORIES')
NODES_WORKSHEET_TITLE = getattr(settings, 'NODES_WORKSHEET_TITLE', 'NODES')
STYLES_WORKSHEET_TITLE = getattr(settings, 'STYLES_WORKSHEET_TITLE', 'STYLES')

HASH_SPREADSHEET_NODES_TABLE_TO_JSON = {
    1: "name",
    2: "categories",
    3: "importance",
    4: "short_description",
    5: "long_description",
    6: "context_url",
    7: "credit",
    8: "node_style",
    9: "label_style",
}

HASH_SPREADSHEET_CATEGORIES_TABLE_TO_JSON = {
    1: "name",
    2: "node_style",
    3: "label_style",
}
