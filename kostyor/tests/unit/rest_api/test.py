import json
import unittest

from flask import wrappers
from keystoneauth1 import exceptions
import mock

from kostyor.inventory import discover
from kostyor.rest_api import app


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
        self.driver_init_kwargs = {
            'username': 'admin',
            'password': 'qwerty',
            'tenant_name': 'admin',
            'auth_url': 'http://9.9.9.9'
        }

    @mock.patch('kostyor.rest_api.discovery_drivers')
    def test_get_discovery_methods(
            self,
            fake_discovery_drivers):
        methods = ['method1', 'method2']
        fake_discovery_drivers.return_value = methods
        res = self.app.get('/discovery-methods')
        self.assertEqual(200, res.status_code)
        received = res.get_json()
        self.assertEqual(methods, received)

    @mock.patch('kostyor.db.api.get_cluster')
    def test_get_upgrade_versions(self, fake_db_get_cluster):
        fake_db_get_cluster.return_value = {'version': 'liberty'}
        res = self.app.get('/upgrade-versions/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)
        received = res.get_json()
        self.assertEqual(['mitaka', 'newton', 'ocata'], received)

    @mock.patch('stevedore.driver.DriverManager')
    @mock.patch('kostyor.rest_api.discovery_drivers')
    @mock.patch('kostyor.resources.discover._create_cluster')
    def test_discover_cluster_supported_method_success(self,
                                                       fake_create_cluster,
                                                       fake_discovery_drivers,
                                                       fake_driver_manager):
        cluster = {
            'id': 'cluster-id',
            'name': 'test-cluster',
            'version': 'mitaka',
            'status': 'READY_FOR_UPGRADE',
        }
        fake_create_cluster.return_value = cluster
        fake_discovery_drivers.return_value = ['openstack', ]
        driver = discover.OpenStackServiceDiscovery()
        driver.discover = mock.Mock(return_value={
            'hosts': {
                '1.2.3.4': [{'name': 'nova-api'}, ]
            }
        })
        fake_driver_manager.return_value.driver = driver

        res = self.app.post('/discover-cluster',
                            data=self.discover_cluster_request_data)

        self.assertEqual(201, res.status_code)
        data = res.get_json()
        self.assertEqual(cluster, data)

        fake_discovery_drivers.assert_called_once_with()
        fake_driver_manager.assert_called_once_with(
            namespace='kostyor.discovery_drivers',
            name='openstack',
            invoke_on_load=True,
            invoke_kwds=self.driver_init_kwargs)
        driver.discover.assert_called_once_with()
        fake_create_cluster.assert_called_once_with(
            'test-cluster',
            driver.discover.return_value)

    def test_discover_cluster_unsupported_method_error_response(self):
        res = self.app.post('/discover-cluster',
                            data={'method': 'unsupported'})
        self.assertEqual(404, res.status_code)

    @mock.patch('stevedore.driver.DriverManager')
    @mock.patch('kostyor.rest_api.discovery_drivers')
    def test_discover_cluster_discovery_failed_error_response(
            self,
            fake_discovery_drivers,
            fake_driver_manager):
        fake_discovery_drivers.return_value = ['openstack', ]
        driver = discover.OpenStackServiceDiscovery()
        driver.discover = mock.Mock(side_effect=exceptions.Unauthorized())
        fake_driver_manager.return_value.driver = driver

        res = self.app.post('/discover-cluster',
                            data=self.discover_cluster_request_data)

        self.assertEqual(401, res.status_code)

        fake_discovery_drivers.assert_called_once_with()
        fake_driver_manager.assert_called_once_with(
            namespace='kostyor.discovery_drivers',
            name='openstack',
            invoke_on_load=True,
            invoke_kwds=self.driver_init_kwargs)
        driver.discover.assert_called_once_with()

    @mock.patch('stevedore.driver.DriverManager')
    @mock.patch('kostyor.rest_api.discovery_drivers')
    def test_discover_cluster_driver_load_failed_error_response(
            self,
            fake_discovery_drivers,
            fake_ext_manager):
        fake_discovery_drivers.return_value = ['openstack', ]
        fake_ext_manager.side_effect = Exception("Cannot load driver.")

        res = self.app.post('/discover-cluster',
                            data=self.discover_cluster_request_data)

        self.assertEqual(404, res.status_code)
        fake_discovery_drivers.assert_called_once_with()
        fake_ext_manager.assert_called_once_with(
            namespace='kostyor.discovery_drivers',
            name='openstack',
            invoke_on_load=True,
            invoke_kwds=self.driver_init_kwargs)
