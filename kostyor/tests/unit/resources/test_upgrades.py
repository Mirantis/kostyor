import json
import datetime

import mock
import oslotest.base
import stevedore

from kostyor.common import constants, exceptions
from kostyor.rest_api import app
from kostyor.resources import Upgrade


class TestUpgradesEndpoint(oslotest.base.BaseTestCase):

    def setUp(self):
        super(TestUpgradesEndpoint, self).setUp()
        self.app = app.test_client()
        self.fake_upgrade = {
            'id': 'd8e98946-5a46-4516-9447-d16deb1d878b',
            'cluster_id': 'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161',
            'from_version': constants.MITAKA,
            'to_version': constants.NEWTON,
            'status': constants.UPGRADE_IN_PROGRESS,
            'upgrade_start_time': datetime.datetime.utcnow(),
            'upgrade_end_time': datetime.datetime.utcnow(),
        }

        self.engine_ext = stevedore.extension.Extension(
            name='node-by-node',
            entry_point=None,
            plugin=mock.Mock(),
            obj=None,
        )
        patcher = mock.patch(
            'kostyor.resources.upgrades._SUPPORTED_ENGINES',
            stevedore.ExtensionManager.make_test_instance(
                extensions=[self.engine_ext],
            )
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _assert_upgrades(self, db_instance, api_instance):
        # timestampes in db instance are represented as datetime objects
        # while in api instance - it's an isoformated string.
        self.assertEqual(
            db_instance.pop('upgrade_start_time').isoformat(),
            api_instance.pop('upgrade_start_time'))
        self.assertEqual(
            db_instance.pop('upgrade_end_time').isoformat(),
            api_instance.pop('upgrade_end_time'))

        # we dealt with timestamps so now we can compare two dicts as is
        self.assertEqual(db_instance, api_instance)

    @mock.patch('kostyor.db.api.get_upgrades')
    def test_get_upgrades(self, fake_db_get_upgrades):
        fake_upgrade_2 = self.fake_upgrade.copy()
        fake_upgrade_2['id'] = 'eb1ee034-89c2-4b2b-9417-ed514c59dd0f'

        expected = [self.fake_upgrade, fake_upgrade_2]
        fake_db_get_upgrades.return_value = expected

        resp = self.app.get('/upgrades')
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        for exp, rec in zip(expected, received):
            self._assert_upgrades(exp, rec)

        fake_db_get_upgrades.assert_called_once_with()

    @mock.patch('kostyor.db.api.get_upgrade')
    def test_get_upgrade(self, fake_db_get_upgrade):
        fake_db_get_upgrade.return_value = self.fake_upgrade

        resp = self.app.get('/upgrades/d8e98946-5a46-4516-9447-d16deb1d878b')
        self.assertEqual(200, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

    @mock.patch('kostyor.db.api.get_upgrade')
    def test_get_upgrade_404(self, fake_db_get_upgrade):
        fake_db_get_upgrade.return_value = None

        resp = self.app.get('/upgrades/123')
        self.assertEqual(404, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self.assertEqual({'message': 'Upgrade 123 not found.'}, received)

    @mock.patch('kostyor.db.api.get_cluster')
    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades(self, fake_create_upgrade, _):
        fake_create_upgrade.return_value = self.fake_upgrade

        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': constants.NEWTON,
                'driver': 'noop',
            })
        )
        self.assertEqual(201, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

        self.assertEqual({}, self.engine_ext.plugin.call_args[0][1].parameters)
        fake_create_upgrade.assert_called_once_with(
            self.fake_upgrade['cluster_id'],
            constants.NEWTON,
        )
        self.engine_ext.plugin.assert_called_once_with(
            self.fake_upgrade,
            mock.ANY,
        )
        self.engine_ext.plugin().start.assert_called_once_with()

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_no_to_version(self, fake_create_upgrade):
        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'driver': 'noop',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cannot create an upgrade task, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'to_version': ['required field']},
        }

        self.assertEqual(expected_error, error)
        self.assertFalse(fake_create_upgrade.called)

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_no_cluster_id(self, fake_create_upgrade):
        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'to_version': constants.NEWTON,
                'driver': 'noop',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cannot create an upgrade task, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'cluster_id': ['required field']},
        }

        self.assertEqual(expected_error, error)
        self.assertFalse(fake_create_upgrade.called)

    @mock.patch('kostyor.db.api.get_cluster')
    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_no_driver(self, fake_createupgrade, _):
        # TODO: Reimplement test to check that 400 Bad Request is returned
        #       once 'driver' is mandatory parameter.

        fake_createupgrade.return_value = self.fake_upgrade

        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': constants.NEWTON,
            })
        )
        self.assertEqual(201, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

        fake_createupgrade.assert_called_once_with(
            self.fake_upgrade['cluster_id'],
            constants.NEWTON,
        )
        self.engine_ext.plugin.assert_called_once_with(
            self.fake_upgrade,
            mock.ANY,
        )
        self.engine_ext.plugin().start.assert_called_once_with()

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_wrong_to_version(self, fake_db_create_upgrade):
        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': 'unsupported-value',
                'driver': 'noop',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cannot create an upgrade task, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'to_version': ['unallowed value unsupported-value']},
        }
        self.assertEqual(expected_error, error)
        self.assertFalse(fake_db_create_upgrade.called)

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_cluster_not_found(self, fake_create_upgrade):
        fake_create_upgrade.side_effect = exceptions.ClusterNotFound(
            'Cluster "edac7d7c-cdfc-4fbe-b194-7b1ffdf21161" not found.'
        )

        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': constants.NEWTON,
                'driver': 'noop',
            })
        )
        self.assertEqual(404, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message':
                'Cluster "edac7d7c-cdfc-4fbe-b194-7b1ffdf21161" not found.'
        }
        self.assertEqual(expected_error, error)

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_cluster_version_unknown(self, fake_create_upgrade):
        fake_create_upgrade.side_effect = exceptions.ClusterVersionIsUnknown(
            'Cluster version is unknown.'
        )

        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': constants.NEWTON,
                'driver': 'noop',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message': 'Cluster version is unknown.'
        }
        self.assertEqual(expected_error, error)

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_cluster_lower_version(self, fake_create_upgrade):
        fake_create_upgrade.side_effect = \
            exceptions.CannotUpgradeToLowerVersion(
                'Upgrade procedure from "mitaka" to "libery" is not allowed.'
            )

        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': constants.LIBERTY,
                'driver': 'noop',
            })
        )
        self.assertEqual(400, resp.status_code)

        error = json.loads(resp.get_data(as_text=True))
        expected_error = {
            'message':
                'Upgrade procedure from "mitaka" to "libery" is not allowed.',
        }
        self.assertEqual(expected_error, error)

    @mock.patch('kostyor.db.api.get_cluster')
    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_post_upgrades_params(self, fake_create_upgrade, _):
        fake_create_upgrade.return_value = self.fake_upgrade

        resp = self.app.post(
            '/upgrades',
            content_type='application/json',
            data=json.dumps({
                'cluster_id': self.fake_upgrade['cluster_id'],
                'to_version': constants.NEWTON,
                'driver': 'noop',
                'parameters': {
                    'x': 42,
                    'y': 'do nothing at all'
                }
            })
        )
        self.assertEqual(201, resp.status_code)

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

        fake_create_upgrade.assert_called_once_with(
            self.fake_upgrade['cluster_id'],
            constants.NEWTON,
        )
        self.assertEqual({
            'x': 42,
            'y': 'do nothing at all'
        }, self.engine_ext.plugin.call_args[0][1].parameters)
        self.engine_ext.plugin.assert_called_once_with(
            self.fake_upgrade,
            mock.ANY,
        )
        self.engine_ext.plugin().start.assert_called_once_with()

    def _make_put_upgrade(self, action, side_effect=None):
        action_fn = mock.Mock(
            return_value=self.fake_upgrade,
            side_effect=side_effect)

        with mock.patch.dict(Upgrade._actions, {action: action_fn}):
            resp = self.app.put(
                '/upgrades/d8e98946-5a46-4516-9447-d16deb1d878b',
                content_type='application/json',
                data=json.dumps({
                    'cluster_id': self.fake_upgrade['cluster_id'],
                    'action': action,
                })
            )
            return resp, action_fn

    def test_put_upgrade_cancel(self):
        resp, action_fn = self._make_put_upgrade('cancel')

        self.assertEqual(200, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

    def test_put_upgrade_cancel_cluster_not_found(self):
        resp, action_fn = self._make_put_upgrade(
            'cancel', exceptions.ClusterNotFound('cluster not found'))

        self.assertEqual(404, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        expected_error = {'message': 'cluster not found'}
        self.assertEqual(expected_error, received)

    def test_put_upgrade_pause(self):
        resp, action_fn = self._make_put_upgrade('pause')

        self.assertEqual(200, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

    def test_put_upgrade_pause_cluster_not_found(self):
        resp, action_fn = self._make_put_upgrade(
            'pause', exceptions.ClusterNotFound('cluster not found'))

        self.assertEqual(404, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        expected_error = {'message': 'cluster not found'}
        self.assertEqual(expected_error, received)

    def test_put_upgrade_continue(self):
        resp, action_fn = self._make_put_upgrade('continue')

        self.assertEqual(200, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

    def test_put_upgrade_continue_cluster_not_found(self):
        resp, action_fn = self._make_put_upgrade(
            'continue', exceptions.ClusterNotFound('cluster not found'))

        self.assertEqual(404, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        expected_error = {'message': 'cluster not found'}
        self.assertEqual(expected_error, received)

    def test_put_upgrade_rollback(self):
        resp, action_fn = self._make_put_upgrade('rollback')

        self.assertEqual(200, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        self._assert_upgrades(self.fake_upgrade, received)

    def test_put_upgrade_rollback_cluster_not_found(self):
        resp, action_fn = self._make_put_upgrade(
            'rollback', exceptions.ClusterNotFound('cluster not found'))

        self.assertEqual(404, resp.status_code)
        action_fn.assert_called_once_with(
            'edac7d7c-cdfc-4fbe-b194-7b1ffdf21161')

        received = json.loads(resp.get_data(as_text=True))
        expected_error = {'message': 'cluster not found'}
        self.assertEqual(expected_error, received)

    def test_put_upgrade_unsupported(self):
        resp, action_fn = self._make_put_upgrade('unsupported')

        self.assertEqual(400, resp.status_code)
        self.assertFalse(action_fn.called)

        received = json.loads(resp.get_data(as_text=True))
        error = {
            'message': 'Cannot update an upgrade task, passed data are '
                       'incorrect. See "errors" attribute for details.',
            'errors': {'action': [u'unallowed value unsupported']},
        }
        self.assertEqual(error, received)
