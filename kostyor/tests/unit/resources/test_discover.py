import json

import mock
import oslotest.base
import stevedore

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

    @mock.patch(
        'kostyor.resources.discover.dbapi.discover_cluster', return_value={
            'name': 'mycluster',
            'version': 'newton',
            'status': 'READY FOR UPGRADE',
        }
    )
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
