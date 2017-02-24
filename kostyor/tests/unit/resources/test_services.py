import json

import mock
import oslotest.base

from kostyor.common import constants, exceptions
from kostyor.rest_api import app


class TestServicesEndpoint(oslotest.base.BaseTestCase):

    def setUp(self):
        super(TestServicesEndpoint, self).setUp()
        self.app = app.test_client()
        self.fake_host = {
            'id': '1111',
            'hostname': 'hostname_1',
            'cluster_id': '1234'
        }

    @mock.patch('kostyor.db.api.get_services_by_host')
    @mock.patch('kostyor.db.api.get_hosts_by_cluster')
    def test_service_list_cluster_exists_success(self,
                                                 get_hosts_by_cluster,
                                                 get_services_by_host):
        fake_nova_api = {
            'id': 'nova-api-3333',
            'name': 'nova-api',
            'version': constants.MITAKA,
            'hosts': ['1111'],
        }
        fake_keystone_api = fake_nova_api.copy()
        fake_keystone_api['id'] = 'keystone-api-4444'
        fake_keystone_api['name'] = 'keystone-api'
        get_hosts_by_cluster.return_value = [self.fake_host]
        get_services_by_host.return_value = [fake_nova_api, fake_keystone_api]

        resp = self.app.get('/clusters/1234/services')
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self.assertEqual([fake_keystone_api, fake_nova_api], received)

        get_hosts_by_cluster.assert_called_once_with('1234')
        get_services_by_host.assert_called_once_with('1111')

    @mock.patch('kostyor.db.api.get_services_by_host')
    @mock.patch('kostyor.db.api.get_hosts_by_cluster')
    def test_service_list_wrong_cluster_id_404(self,
                                               get_hosts_by_cluster,
                                               get_services_by_host):
        get_hosts_by_cluster.side_effect = \
            exceptions.ClusterNotFound('cluster not found')

        resp = self.app.get('/clusters/fake/services')
        self.assertEqual(404, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        error = {'message': 'cluster not found'}
        self.assertEqual(error, received)

        get_hosts_by_cluster.assert_called_once_with('fake')
        self.assertFalse(get_services_by_host.called)
