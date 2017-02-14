import json
import unittest

from flask import wrappers
import mock

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

    @mock.patch('kostyor.db.api.get_cluster')
    def test_get_upgrade_versions(self, fake_db_get_cluster):
        fake_db_get_cluster.return_value = {'version': 'liberty'}
        res = self.app.get('/upgrade-versions/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)
        received = res.get_json()
        self.assertEqual(['mitaka', 'newton', 'ocata'], received)
