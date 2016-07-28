import json
import mock
import sys
import unittest
sys.modules['kostyor.conf'] = mock.Mock()
from kostyor.rest_api import app

class KostyorRestAPITest(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.cluster_id = 123

    @mock.patch('kostyor.db.api.get_cluster_status')
    def test_get_cluster_status(self, fake_db_get_cluster_status):
        expected = {'status': 'done', 'name': 'tmp', 'id': '123'}
        fake_db_get_cluster_status.return_value = expected
        res = self.app.get('/cluster-status/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)
        data = res.data.decode('utf-8')
        received = json.loads(data)
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.get_cluster_status')
    def test_get_cluster_status_404(self, fake_db_get_cluster_status):
        fake_db_get_cluster_status.return_value = None
        res = self.app.get('/cluster-status/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.db.api.get_upgrade_status')
    def test_get_upgrade_status(self, fake_db_get_upgrade_status):
        expected = {'status': 'status',
                    'id': '123'}
        fake_db_get_upgrade_status.return_value = expected
        res = self.app.get('/upgrade-status/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)
        data = res.data.decode('utf-8')
        received = json.loads(data)
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.get_upgrade_status')
    def test_get_upgrade_status_404(self, fake_db_get_upgrade_status):
        fake_db_get_upgrade_status.return_value = None
        res = self.app.get('/upgrade-status/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.db.api.get_discovery_methods')
    def test_get_discovery_methods_default_only(self,
                    fake_conf_get_discovery_methods):
        methods = ['method1', 'method2']
        fake_conf_get_discovery_methods.return_value = methods
        res = self.app.get('/discovery-methods')
        str_data = res.data.decode('utf-8')
        data = json.loads(str_data)
        received = data['items']
        expected = [{'method': method} for method in methods]
        self.assertEqual(200, res.status_code)
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.get_upgrade_versions')
    def test_get_upgrade_versions(self, fake_db_get_upgrade_versions):
        expected = {'items': [
                    {'version': 'version1'},
                    {'version': 'version2'}
                    ]
        }

        fake_db_get_upgrade_versions.return_value = expected
        res = self.app.get('/upgrade-versions/{}'.format(self.cluster_id))
        data = res.data.decode('utf-8')
        received = json.loads(data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.create_discovery_method')
    def test_create_disc_method_404(self, fake_db_create_disc_method):
        fake_db_create_disc_method.return_value = None
        res = self.app.post('/discover-cluster')
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.db.api.create_discovery_method')
    def test_create_disc_method(self, fake_db_create_disc_method):
        expected = {'id': '1', 'method': 'method'}

        fake_db_create_disc_method.return_value = expected
        res = self.app.post('/discover-cluster')
        data = res.data.decode('utf-8')
        received = json.loads(data)
        self.assertEqual(201, res.status_code)
        self.assertEqual(expected, received)

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_create_cluster_upgrade_404(self, fake_db_create_cluster_upgrade):
        fake_db_create_cluster_upgrade.return_value = None
        res = self.app.post('/upgrade-cluster/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.db.api.create_cluster_upgrade')
    def test_create_cluster_upgrade(self, fake_db_create_cluster_upgrade):
        expected = {'id': self.cluster_id, 'status': 'upgrading'}

        fake_db_create_cluster_upgrade.return_value = expected
        res = self.app.post('/upgrade-cluster/{}'.format(self.cluster_id))
        data = res.data.decode('utf-8')
        received = json.loads(data)
        self.assertEqual(201, res.status_code)
        self.assertEqual(expected, received)

    @mock.patch('kostyor.inventory.upgrades.cancel_upgrade')
    @mock.patch('kostyor.db.api.cancel_cluster_upgrade')
    def test_cancel_cluster_upgrade_404(self,
            fake_db_cancel_cluster_upgrade, fake_inventory_cancel_upgrade):
        fake_db_cancel_cluster_upgrade.return_value = None
        fake_inventory_cancel_upgrade.return_value = 0
        res = self.app.put('/upgrade-cancel/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.cancel_upgrade')
    @mock.patch('kostyor.db.api.cancel_cluster_upgrade')
    def test_cancel_cluster_upgrade_on_inventory_failure(self,
            fake_db_cancel_cluster_upgrade, fake_inventory_cancel_upgrade):
        fake_db_cancel_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_cancel_upgrade.return_value = 1
        res = self.app.put('/upgrade-cancel/{}'.format(self.cluster_id))
        self.assertEqual(500, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.cancel_upgrade')
    @mock.patch('kostyor.db.api.cancel_cluster_upgrade')
    def test_cancel_cluster_upgrade(self,
            fake_db_cancel_cluster_upgrade, fake_inventory_cancel_upgrade):
        fake_db_cancel_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_cancel_upgrade.return_value = 0
        res = self.app.put('/upgrade-cancel/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.continue_upgrade')
    @mock.patch('kostyor.db.api.continue_cluster_upgrade')
    def test_continue_cluster_upgrade_404(self,
            fake_db_continue_cluster_upgrade, fake_inventory_continue_upgrade):
        fake_db_continue_cluster_upgrade.return_value = None
        fake_inventory_continue_upgrade.return_value = 0
        res = self.app.put('/upgrade-continue/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.continue_upgrade')
    @mock.patch('kostyor.db.api.continue_cluster_upgrade')
    def test_continue_cluster_upgrade_on_inventory_failure(self,
            fake_db_continue_cluster_upgrade, fake_inventory_continue_upgrade):
        fake_db_continue_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_continue_upgrade.return_value = 1
        res = self.app.put('/upgrade-continue/{}'.format(self.cluster_id))
        self.assertEqual(500, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.continue_upgrade')
    @mock.patch('kostyor.db.api.continue_cluster_upgrade')
    def test_continue_cluster_upgrade(self,
            fake_db_continue_cluster_upgrade, fake_inventory_continue_upgrade):
        fake_db_continue_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_continue_upgrade.return_value = 0
        res = self.app.put('/upgrade-continue/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.pause_upgrade')
    @mock.patch('kostyor.db.api.pause_cluster_upgrade')
    def test_pause_cluster_upgrade_404(self,
            fake_db_pause_cluster_upgrade, fake_inventory_pause_upgrade):
        fake_db_pause_cluster_upgrade.return_value = None
        fake_inventory_pause_upgrade.return_value = 0
        res = self.app.put('/upgrade-pause/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.pause_upgrade')
    @mock.patch('kostyor.db.api.pause_cluster_upgrade')
    def test_pause_cluster_upgrade_on_inventory_failure(self,
            fake_db_pause_cluster_upgrade, fake_inventory_pause_upgrade):
        fake_db_pause_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_pause_upgrade.return_value = 1
        res = self.app.put('/upgrade-pause/{}'.format(self.cluster_id))
        self.assertEqual(500, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.pause_upgrade')
    @mock.patch('kostyor.db.api.pause_cluster_upgrade')
    def test_pause_cluster_upgrade(self,
            fake_db_pause_cluster_upgrade, fake_inventory_pause_upgrade):
        fake_db_pause_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'paused'}
        fake_inventory_pause_upgrade.return_value = 0
        res = self.app.put('/upgrade-pause/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.rollback_upgrade')
    @mock.patch('kostyor.db.api.rollback_cluster_upgrade')
    def test_rollback_cluster_upgrade_404(self,
            fake_db_rollback_cluster_upgrade, fake_inventory_rollback_upgrade):
        fake_db_rollback_cluster_upgrade.return_value = None
        fake_inventory_rollback_upgrade.return_value = 0
        res = self.app.put('/upgrade-rollback/{}'.format(self.cluster_id))
        self.assertEqual(404, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.rollback_upgrade')
    @mock.patch('kostyor.db.api.rollback_cluster_upgrade')
    def test_rollback_cluster_upgrade_on_inventory_failure(self,
            fake_db_rollback_cluster_upgrade, fake_inventory_rollback_upgrade):
        fake_db_rollback_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_rollback_upgrade.return_value = 1
        res = self.app.put('/upgrade-rollback/{}'.format(self.cluster_id))
        self.assertEqual(500, res.status_code)

    @mock.patch('kostyor.inventory.upgrades.rollback_upgrade')
    @mock.patch('kostyor.db.api.rollback_cluster_upgrade')
    def test_rollback_cluster_upgrade(self,
            fake_db_rollback_cluster_upgrade, fake_inventory_rollback_upgrade):
        fake_db_rollback_cluster_upgrade.return_value = {'id': self.cluster_id,
                                                       'status': 'canceling'}
        fake_inventory_rollback_upgrade.return_value = 0
        res = self.app.put('/upgrade-rollback/{}'.format(self.cluster_id))
        self.assertEqual(200, res.status_code)
