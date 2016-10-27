import datetime

import mock
import oslotest.base

from kostyor.common import constants
from kostyor.rpc import tasks
from kostyor.upgrades import Engine, UpgradeDriver


class MockUpgradeDriver(UpgradeDriver):

    supports_upgrade_rollback = mock.Mock(return_value=False)
    stop_upgrade = mock.Mock(return_value=tasks.noop.si())
    start_upgrade = mock.Mock(return_value=tasks.noop.si())
    pause_upgrade = mock.Mock(return_value=tasks.noop.si())
    cancel_upgrade = mock.Mock(return_value=tasks.noop.si())
    rollback_upgrade = mock.Mock(return_value=tasks.noop.si())
    continue_upgrade = mock.Mock(return_value=tasks.noop.si())
    pre_host_upgrade_hook = mock.Mock(return_value=tasks.noop.si())
    post_host_upgrade_hook = mock.Mock(return_value=tasks.noop.si())
    pre_service_upgrade_hook = mock.Mock(return_value=tasks.noop.si())
    post_service_upgrade_hook = mock.Mock(return_value=tasks.noop.si())


class TestEngine(oslotest.base.BaseTestCase):

    def setUp(self):
        super(TestEngine, self).setUp()
        self.upgrade = {
            'id': 'd174522c-95fc-4996-8dfa-0c2405a3b0c1',
            'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687',
            'from_version': constants.MITAKA,
            'to_version': constants.NEWTON,
            'upgrade_start_time': datetime.datetime.utcnow(),
            'upgrade_end_time': None,
            'status': constants.READY_FOR_UPGRADE,
        }
        self.hosts = [
            {'id': '5708c51f-5421-4ecd-9a9e-000000000001',
             'hostname': 'host-1',
             'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687'},
            {'id': '5708c51f-5421-4ecd-9a9e-000000000002',
             'hostname': 'host-2',
             'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687'},
            {'id': '5708c51f-5421-4ecd-9a9e-000000000003',
             'hostname': 'host-3',
             'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687'},
        ]
        self.engine = Engine(self.upgrade)

        patcher = mock.patch('kostyor.upgrades.engine.dbapi')
        self.addCleanup(patcher.stop)

        self.dbapi = patcher.start()
        self.dbapi.get_hosts_by_cluster = mock.Mock(return_value=self.hosts)

    def test_common_assignment(self):
        services = {
            # compute
            '5708c51f-5421-4ecd-9a9e-000000000001': [
                {'name': 'nova-compute',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000001',
                 'version': constants.MITAKA},
                {'name': 'neutron-linuxbridge-agent',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000001',
                 'version': constants.MITAKA},
            ],

            # controller
            '5708c51f-5421-4ecd-9a9e-000000000002': [
                {'name': 'nova-spicehtml5proxy',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'nova-scheduler',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'nova-api',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'nova-conductor',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},

                {'name': 'keystone-wsgi-public',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'keystone-wsgi-admin',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},

                {'name': 'neutron-server',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'neutron-linuxbridge-agent',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'neutron-l3-agent',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'neutron-dhcp-agent',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'neutron-metering-agent',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'neutron-metadata-agent',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'neutron-ns-metadata-proxy',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},

                {'name': 'glance-registry',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'glance-api',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},

                {'name': 'heat-api',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'heat-api-cloudwatch',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'heat-api-cfn',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'heat-engine',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},

                {'name': 'cinder-api',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
                {'name': 'cinder-scheduler',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                 'version': constants.MITAKA},
            ],

            # storage
            '5708c51f-5421-4ecd-9a9e-000000000003': [
                {'name': 'cinder-volume',
                 'host_id': '5708c51f-5421-4ecd-9a9e-000000000003',
                 'version': constants.MITAKA},
            ],
        }

        # mock dbapi to return predefined services
        def get_services_by_host(host):
            return services[host]
        self.dbapi.get_services_by_host = get_services_by_host
        self.engine.driver = MockUpgradeDriver()

        self.engine.start()

        expected_service_calls = [
            # controller
            mock.call(self.upgrade,
                      {'name': 'keystone-wsgi-admin',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'keystone-wsgi-public',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'glance-api',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'glance-registry',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-conductor',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-scheduler',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-spicehtml5proxy',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-api',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-server',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-linuxbridge-agent',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-l3-agent',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-dhcp-agent',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-metering-agent',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-metadata-agent',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-ns-metadata-proxy',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-api',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-scheduler',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-engine',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api-cfn',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api-cloudwatch',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000002',
                       'version': constants.MITAKA}),
            # compute
            mock.call(self.upgrade,
                      {'name': 'nova-compute',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000001',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-linuxbridge-agent',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000001',
                       'version': constants.MITAKA}),

            # storage
            mock.call(self.upgrade,
                      {'name': 'cinder-volume',
                       'host_id': '5708c51f-5421-4ecd-9a9e-000000000003',
                       'version': constants.MITAKA}),
        ]
        self.assertEqual(
            expected_service_calls,
            self.engine.driver.pre_service_upgrade_hook.call_args_list)
        self.assertEqual(
            expected_service_calls,
            self.engine.driver.start_upgrade.call_args_list)
        self.assertEqual(
            expected_service_calls,
            self.engine.driver.post_service_upgrade_hook.call_args_list)

        expected_host_calls = [
            mock.call(self.upgrade,
                      {'hostname': 'host-2',
                       'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687',
                       'id': '5708c51f-5421-4ecd-9a9e-000000000002'}),
            mock.call(self.upgrade,
                      {'hostname': 'host-1',
                       'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687',
                       'id': '5708c51f-5421-4ecd-9a9e-000000000001'}),
            mock.call(self.upgrade,
                      {'hostname': 'host-3',
                       'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687',
                       'id': '5708c51f-5421-4ecd-9a9e-000000000003'}),
        ]
        self.assertEqual(
            expected_host_calls,
            self.engine.driver.pre_host_upgrade_hook.call_args_list)
        self.assertEqual(
            expected_host_calls,
            self.engine.driver.post_host_upgrade_hook.call_args_list)
