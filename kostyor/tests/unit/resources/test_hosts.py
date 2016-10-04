import json

import mock
import oslotest.base

from kostyor.common import exceptions
from kostyor.rest_api import app


class TestHostsEndpoint(oslotest.base.BaseTestCase):

    def setUp(self):
        super(TestHostsEndpoint, self).setUp()
        self.app = app.test_client()
        self.fake_host = {
            'id': '1111',
            'hostname': 'hostname_1',
            'cluster_id': '1234'
        }

    @mock.patch('kostyor.db.api.get_hosts_by_cluster')
    def test_host_list_cluster_exists_success(self, get_hosts_by_cluster):
        fake_host_2 = {
            'id': '2222',
            'hostname': 'hostname_2',
            'cluster_id': '1234'
        }
        fake_hosts = [self.fake_host, fake_host_2]
        get_hosts_by_cluster.return_value = fake_hosts

        resp = self.app.get('/clusters/1234/hosts')
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self.assertEqual(fake_hosts, received)

        get_hosts_by_cluster.assert_called_once_with('1234')

    @mock.patch('kostyor.db.api.get_hosts_by_cluster')
    def test_host_list_wrong_cluster_id_404(self, get_hosts_by_cluster):
        get_hosts_by_cluster.side_effect = \
            exceptions.ClusterNotFound('cluster not found')

        resp = self.app.get('/clusters/fake/hosts')
        self.assertEqual(404, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        error = {'message': 'cluster not found'}
        self.assertEqual(error, received)

        get_hosts_by_cluster.assert_called_once_with('fake')
