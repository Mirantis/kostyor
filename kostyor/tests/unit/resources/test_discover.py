import json

import mock
import oslotest.base
import stevedore

from kostyor.common import constants
from kostyor.resources import discover
from kostyor.rest_api import app


class TestDiscoverEndpoint(oslotest.base.BaseTestCase):

    def setUp(self):
        super(TestDiscoverEndpoint, self).setUp()
        self.app = app.test_client()

        self.discover_ext = stevedore.extension.Extension(
            name='test-discover',
            entry_point=None,
            plugin=mock.Mock(),
            obj=None,
        )

        ext_manager = stevedore.ExtensionManager.make_test_instance(
            extensions=[self.discover_ext],
        )
        patcher = mock.patch(
            'kostyor.resources.discover._SUPPORTED_DRIVERS', ext_manager)
        patcher.start()
        self.addCleanup(patcher.stop)

        # Class attributes are evaluated only once on module import time.
        # So patching global ExtensionManager above is not enough to make
        # things correct.
        patcher = mock.patch.dict(
            discover.Discover._schema,
            {
                'method': {
                    'type': 'string',
                    'required': True,
                    'allowed': ext_manager.names(),
                }
            })
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_post_name_is_required(self):
        resp = self.app.post(
            '/clusters/discover',
            content_type='application/json',
            data=json.dumps({
                'method': 'test-discover',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cannot discover a cluster, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'name': ['required field']},
        }

        self.assertEqual(expected_error, error)

    def test_post_method_is_required(self):
        resp = self.app.post(
            '/clusters/discover',
            content_type='application/json',
            data=json.dumps({
                'name': 'mycluster',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cannot discover a cluster, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'method': ['required field']},
        }

        self.assertEqual(expected_error, error)

    def test_post_method_is_enum(self):
        resp = self.app.post(
            '/clusters/discover',
            content_type='application/json',
            data=json.dumps({
                'name': 'mycluster',
                'method': 'does-not-exist',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cannot discover a cluster, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'method': ['unallowed value does-not-exist']},
        }

        self.assertEqual(expected_error, error)

    @mock.patch('kostyor.resources.discover._create_cluster', return_value={
        'name': 'mycluster',
        'version': 'newton',
        'status': 'READY FOR UPGRADE',
    })
    def test_post_extension_is_called(self, _):
        resp = self.app.post(
            '/clusters/discover',
            content_type='application/json',
            data=json.dumps({
                'name': 'mycluster',
                'method': 'test-discover',
                'parameters': {
                    'a': 1,
                    'b': True,
                    'c': 'something',
                }
            })
        )
        self.assertEqual(201, resp.status_code)

        self.discover_ext.plugin.assert_called_once_with(
            a=1,
            b=True,
            c='something',
        )
        self.discover_ext.plugin().discover.assert_called_once_with()

    def test_get_methods(self):
        resp = self.app.get(
            '/clusters/discover',
            content_type='application/json'
        )
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self.assertEqual(['test-discover'], received)


class TestCreateCluster(oslotest.base.BaseTestCase):

    @mock.patch('kostyor.db.api.create_service')
    @mock.patch('kostyor.db.api.create_host')
    @mock.patch('kostyor.db.api.create_cluster')
    def test_create_cluster(self, create_cluster, create_host, create_service):
        create_cluster.return_value = {
            'id': '35e50132-b725-4d7c-a569-611f84decb37',
            'name': 'mycluster',
            'version': constants.UNKNOWN,
            'status': constants.NOT_READY_FOR_UPGRADE,
        }
        create_host.return_value = {
            'id': 'e9cfae98-1af7-4cb8-9178-37465e48b689',
            'hostname': 'host-a',
            'cluster_id': create_cluster.return_value['id'],
        }
        cluster = discover._create_cluster(
            'mycluster',
            {
                'services': [('host-a', 'nova-api'), ]
            }
        )

        self.assertEqual(cluster, create_cluster.return_value)
        create_cluster.assert_called_once_with(
            'mycluster', constants.UNKNOWN, constants.NOT_READY_FOR_UPGRADE)
        create_host.assert_called_once_with(
            'host-a', create_cluster.return_value['id'])
        create_service.assert_called_once_with(
            'nova-api',
            create_host.return_value['id'],
            create_cluster.return_value['version'],
        )
