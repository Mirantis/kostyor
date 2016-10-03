import json
import sys
import unittest

from flask import wrappers
from keystoneauth1 import exceptions
import mock

from kostyor.rest_api import app
from kostyor.common import constants
sys.modules['kostyor.conf'] = mock.Mock()


class TestResponse(wrappers.Response):
    def get_json(self):
        try:
            data = self.get_data(as_text=True)
            return json.loads(data)
        except ValueError:
            return {}


class KostyorRestAPITest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.response_wrapper = TestResponse
        self.cluster_id = 123
        self.discover_cluster_request_data = {
            'method': 'openstack',
            'cluster_name': 'test-cluster',
            'username': 'admin',
            'password': 'qwerty',
            'tenant_name': 'admin',
            'auth_url': 'http://9.9.9.9',
        }
        self.fake_host = {
            'id': '1111',
            'name': 'hostname_1',
            'cluster_id': '1234'
        }

    @mock.patch('kostyor.db.api.get_upgrade_by_cluster')
    def test_get_upgrade_status_404(self, fake_db_get_upgrade_by_cluster):
        fake_db_get_upgrade_by_cluster.return_value = None
        res = self.app.get('/upgrade-status/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.db.api.get_discovery_methods')
    def test_get_discovery_methods_default_only(
            self,
            fake_conf_get_discovery_methods):
        methods = ['method1', 'method2']
        fake_conf_get_discovery_methods.return_value = methods
        res = self.app.get('/discovery-methods')
        self.assertEqual(200, res.status_code)
        data = res.get_json()
        received = data.get('items')
        expected = [{'method': method} for method in methods]
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.get_cluster')
    def test_get_upgrade_versions(self, fake_db_get_cluster):
        fake_db_get_cluster.return_value = {'version': 'liberty'}
        res = self.app.get('/upgrade-versions/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)
        received = res.get_json()
        self.assertEqual(['mitaka', 'newton'], received)

    @mock.patch('kostyor.db.api.create_discovery_method')
    def test_create_disc_method_404(self, fake_db_create_disc_method):
        fake_db_create_disc_method.return_value = None
        res = self.app.post('/create-discovery-method')
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.db.api.create_discovery_method')
    def test_create_disc_method(self, fake_db_create_disc_method):
        expected = {'id': '1', 'method': 'method'}

        fake_db_create_disc_method.return_value = expected
        res = self.app.post('/create-discovery-method')
        self.assertEqual(201, res.status_code)
        received = res.get_json()
        self.assertEqual(expected, received)

    @mock.patch('keystoneauth1.identity.v2.Password')
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch(
        'kostyor.inventory.discover.OpenStackServiceDiscovery.discover')
    @mock.patch('kostyor.db.api.create_cluster')
    @mock.patch('kostyor.db.api.create_host')
    @mock.patch('kostyor.db.api.create_service')
    def test_discover_cluster_openstack_method_success(self,
                                                       fake_create_service,
                                                       fake_create_host,
                                                       fake_create_cluster,
                                                       fake_discover,
                                                       fake_session,
                                                       fake_password):
        password_mock = mock.Mock()
        fake_password.return_value = password_mock
        fake_discover.return_value = [('1.2.3.4', 'nova-api'), ]
        cluster = {
            'id': 'cluster-id',
            'name': 'test-cluster',
            'version': 'mitaka',
            'status': 'READY_FOR_UPGRADE',
        }
        fake_create_cluster.return_value = cluster
        fake_create_host.return_value = {
            'id': 'host-id',
            'name': '1.2.3.4',
            'cluster_id': 'cluster-id',
        }

        res = self.app.post('/discover-cluster',
                            data=self.discover_cluster_request_data)
        self.assertEqual(201, res.status_code)
        data = res.get_json()
        self.assertEqual(cluster, data)
        fake_password.assert_called_once_with(username='admin',
                                              password='qwerty',
                                              tenant_name='admin',
                                              auth_url='http://9.9.9.9')
        fake_session.assert_called_once_with(auth=password_mock)
        fake_discover.assert_called_once_with()
        fake_create_cluster.assert_called_once_with(
            'test-cluster',
            constants.UNKNOWN,
            constants.NOT_READY_FOR_UPGRADE)
        fake_create_host.assert_called_once_with('1.2.3.4', 'cluster-id')
        fake_create_service.assert_called_once_with(
            'nova-api',
            'host-id',
            constants.UNKNOWN)

    def test_discover_cluster_unsupported_method_error_response(self):
        res = self.app.post('/discover-cluster',
                            data={'method': 'unsupported'})
        self.assertEqual(404, res.status_code)

    @mock.patch('keystoneauth1.identity.v2.Password')
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch(
        'kostyor.inventory.discover.OpenStackServiceDiscovery.discover')
    def test_discover_cluster_discovery_failed_error_response(self,
                                                              fake_discover,
                                                              fake_session,
                                                              fake_password):
        password_mock = mock.Mock()
        fake_password.return_value = password_mock
        fake_discover.side_effect = exceptions.Unauthorized()

        res = self.app.post('/discover-cluster',
                            data=self.discover_cluster_request_data)

        self.assertEqual(401, res.status_code)
        fake_password.assert_called_once_with(username='admin',
                                              password='qwerty',
                                              tenant_name='admin',
                                              auth_url='http://9.9.9.9')
        fake_session.assert_called_once_with(auth=password_mock)
        fake_discover.assert_called_once_with()
