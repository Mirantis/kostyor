import json

import mock
import oslotest.base

from kostyor.common import constants
from kostyor.rest_api import app


class TestClustersEndpoint(oslotest.base.BaseTestCase):

    def setUp(self):
        super(TestClustersEndpoint, self).setUp()
        self.app = app.test_client()

    @mock.patch('kostyor.db.api.get_clusters')
    def test_get_clusters(self, fake_db_get_clusters):
        expected = [
            {
                'id': '11d7f0ab-8aba-4185-a3c3-9604b2ef965e',
                'name': 'test_a',
                'status': constants.READY_FOR_UPGRADE,
                'version': constants.MITAKA,
            },
            {
                'id': '1feef932-e694-48e3-adc9-b85b13a1aa7b',
                'name': 'test_b',
                'status': constants.READY_FOR_UPGRADE,
                'version': constants.NEWTON,
            },
        ]
        fake_db_get_clusters.return_value = expected

        resp = self.app.get('/clusters')
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))['clusters']
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.get_cluster')
    def test_get_cluster_status(self, fake_db_get_cluster):
        expected = {'id': '1feef932-e694-48e3-adc9-b85b13a1aa7b',
                    'name': 'test',
                    'status': constants.READY_FOR_UPGRADE,
                    'version': constants.MITAKA}
        fake_db_get_cluster.return_value = expected

        resp = self.app.get('/clusters/1feef932-e694-48e3-adc9-b85b13a1aa7b')
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.get_cluster')
    def test_get_cluster_404(self, fake_db_get_cluster):
        fake_db_get_cluster.return_value = None

        resp = self.app.get('/clusters/123')
        self.assertEqual(404, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self.assertEqual({'message': 'Cluster 123 not found.'}, received)
