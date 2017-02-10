import datetime

import mock
import oslotest.base

from kostyor.common import constants
from kostyor.rpc import tasks
from kostyor.upgrades import Engine


# We can't inherit 'base.UpgradeDriver' since it requires to implement
# abstract methods, and we are not interested in it. Instead we want
# to mock each interface method in order to trace its calls.
class MockUpgradeDriver(object):

    _methods = [
        'stop_upgrade',
        'start_upgrade',
        'pause_upgrade',
        'cancel_upgrade',
        'rollback_upgrade',
        'continue_upgrade',
        'pre_upgrade_hook',
        'pre_host_upgrade_hook',
        'post_host_upgrade_hook',
        'pre_service_upgrade_hook',
        'post_service_upgrade_hook',
    ]

    def __init__(self):
        for method in self._methods:
            setattr(self, method, mock.Mock(return_value=tasks.noop.si()))
        self.supports_upgrade_rollback = mock.Mock(return_value=False)


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
        self.engine = Engine(self.upgrade, MockUpgradeDriver())

        patcher = mock.patch('kostyor.upgrades.engine.dbapi')
        self.addCleanup(patcher.stop)
        self.dbapi = patcher.start()

    def test_multinode_assignment(self):
        self.dbapi.get_hosts_by_cluster.return_value = [
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

        services = {
            # compute
            '5708c51f-5421-4ecd-9a9e-000000000001': [
                {'name': 'nova-compute',
                 'version': constants.MITAKA},
                {'name': 'neutron-linuxbridge-agent',
                 'version': constants.MITAKA},
            ],

            # controller
            '5708c51f-5421-4ecd-9a9e-000000000002': [
                {'name': 'nova-spicehtml5proxy',
                 'version': constants.MITAKA},
                {'name': 'nova-scheduler',
                 'version': constants.MITAKA},
                {'name': 'nova-api',
                 'version': constants.MITAKA},
                {'name': 'nova-conductor',
                 'version': constants.MITAKA},

                {'name': 'keystone-wsgi-public',
                 'version': constants.MITAKA},
                {'name': 'keystone-wsgi-admin',
                 'version': constants.MITAKA},

                {'name': 'neutron-server',
                 'version': constants.MITAKA},
                {'name': 'neutron-linuxbridge-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-l3-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-dhcp-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-metering-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-metadata-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-ns-metadata-proxy',
                 'version': constants.MITAKA},

                {'name': 'glance-registry',
                 'version': constants.MITAKA},
                {'name': 'glance-api',
                 'version': constants.MITAKA},

                {'name': 'heat-api',
                 'version': constants.MITAKA},
                {'name': 'heat-api-cloudwatch',
                 'version': constants.MITAKA},
                {'name': 'heat-api-cfn',
                 'version': constants.MITAKA},
                {'name': 'heat-engine',
                 'version': constants.MITAKA},

                {'name': 'cinder-api',
                 'version': constants.MITAKA},
                {'name': 'cinder-scheduler',
                 'version': constants.MITAKA},
            ],

            # storage
            '5708c51f-5421-4ecd-9a9e-000000000003': [
                {'name': 'cinder-volume',
                 'version': constants.MITAKA},
            ],
        }

        # mock dbapi to return predefined services
        def get_services_by_host(host):
            return services[host]
        self.dbapi.get_services_by_host = get_services_by_host

        self.engine.start()

        expected_service_calls = [
            # controller
            mock.call(self.upgrade,
                      {'name': 'keystone-wsgi-admin',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'keystone-wsgi-public',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'glance-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'glance-registry',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-conductor',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-scheduler',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-spicehtml5proxy',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-server',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-linuxbridge-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-l3-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-dhcp-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-metering-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-metadata-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-ns-metadata-proxy',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-scheduler',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-engine',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api-cfn',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api-cloudwatch',
                       'version': constants.MITAKA}),
            # compute
            mock.call(self.upgrade,
                      {'name': 'nova-compute',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-linuxbridge-agent',
                       'version': constants.MITAKA}),

            # storage
            mock.call(self.upgrade,
                      {'name': 'cinder-volume',
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

        self.engine.driver.pre_upgrade_hook.assert_called_once_with(
            self.upgrade
        )

    def test_all_in_one_assignment(self):
        self.dbapi.get_hosts_by_cluster.return_value = [
            {'id': '5708c51f-5421-4ecd-9a9e-000000000001',
             'hostname': 'host-1',
             'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687'},
        ]

        services = {
            '5708c51f-5421-4ecd-9a9e-000000000001': [
                {'name': 'nova-spicehtml5proxy',
                 'version': constants.MITAKA},
                {'name': 'nova-scheduler',
                 'version': constants.MITAKA},
                {'name': 'nova-api',
                 'version': constants.MITAKA},
                {'name': 'nova-conductor',
                 'version': constants.MITAKA},
                {'name': 'nova-compute',
                 'version': constants.MITAKA},

                {'name': 'keystone-wsgi-public',
                 'version': constants.MITAKA},
                {'name': 'keystone-wsgi-admin',
                 'version': constants.MITAKA},

                {'name': 'neutron-server',
                 'version': constants.MITAKA},
                {'name': 'neutron-linuxbridge-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-l3-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-dhcp-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-metering-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-metadata-agent',
                 'version': constants.MITAKA},
                {'name': 'neutron-ns-metadata-proxy',
                 'version': constants.MITAKA},

                {'name': 'glance-registry',
                 'version': constants.MITAKA},
                {'name': 'glance-api',
                 'version': constants.MITAKA},

                {'name': 'heat-api',
                 'version': constants.MITAKA},
                {'name': 'heat-api-cloudwatch',
                 'version': constants.MITAKA},
                {'name': 'heat-api-cfn',
                 'version': constants.MITAKA},
                {'name': 'heat-engine',
                 'version': constants.MITAKA},

                {'name': 'cinder-api',
                 'version': constants.MITAKA},
                {'name': 'cinder-scheduler',
                 'version': constants.MITAKA},
                {'name': 'cinder-volume',
                 'version': constants.MITAKA},
            ],
        }

        # mock dbapi to return predefined services
        def get_services_by_host(host):
            return services[host]
        self.dbapi.get_services_by_host = get_services_by_host

        self.engine.start()

        expected_service_calls = [
            mock.call(self.upgrade,
                      {'name': 'keystone-wsgi-admin',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'keystone-wsgi-public',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'glance-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'glance-registry',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-conductor',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-scheduler',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-spicehtml5proxy',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'nova-compute',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-server',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-linuxbridge-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-l3-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-dhcp-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-metering-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-metadata-agent',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'neutron-ns-metadata-proxy',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-scheduler',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'cinder-volume',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-engine',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api-cfn',
                       'version': constants.MITAKA}),
            mock.call(self.upgrade,
                      {'name': 'heat-api-cloudwatch',
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
                      {'hostname': 'host-1',
                       'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687',
                       'id': '5708c51f-5421-4ecd-9a9e-000000000001'}),
        ]
        self.assertEqual(
            expected_host_calls,
            self.engine.driver.pre_host_upgrade_hook.call_args_list)
        self.assertEqual(
            expected_host_calls,
            self.engine.driver.post_host_upgrade_hook.call_args_list)

        self.engine.driver.pre_upgrade_hook.assert_called_once_with(
            self.upgrade
        )
