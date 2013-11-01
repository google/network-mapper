from django.test.client import Client

from core.tests.base import BaseAppengineTestCase
from graph.models import Graph


class GraphBase(BaseAppengineTestCase):

    def create_graph(self, user_id, is_public=False):

        graph = Graph(
            user_id=user_id,
            name='An Other Graph',
            is_public=is_public,
            spreadsheet_id='123456'
        )
        graph.put()
        return graph

    def setUp(self):
        super(GraphBase, self).setUp()
        self.client = Client()
        self.other_public_graph = self.create_graph('999', False)
        self.other_private_graph = self.create_graph('666', True)
        self.url = None
