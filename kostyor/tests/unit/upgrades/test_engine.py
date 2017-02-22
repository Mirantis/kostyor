import datetime

import mock
import oslotest.base

from kostyor.common import constants
from kostyor.rpc import tasks
from kostyor.upgrades import Engine
from kostyor.upgrades.drivers import base as basedriver


# A special version of the driver that mocks driver interface so we can
# track calls to its methods.
class MockUpgradeDriver(basedriver.UpgradeDriver):

    _methods = [
        'pre_upgrade',
        'start',
    ]

    def __new__(cls):
        # Since we don't implement abstract methods but mock them instead,
        # we need to consider everything implemented and do not fail on
        # attempt to create an instance.
        cls.__abstractmethods__ = set()

        instance = super(MockUpgradeDriver, cls).__new__(cls)
        for method in cls._methods:
            setattr(instance, method, mock.Mock(return_value=tasks.noop.si()))
        return instance


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
        hosts = [
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
                {'name': 'nova-compute'},
                {'name': 'neutron-linuxbridge-agent'},
            ],
            # controller
            '5708c51f-5421-4ecd-9a9e-000000000002': [
                {'name': 'nova-spicehtml5proxy'},
                {'name': 'nova-scheduler'},
                {'name': 'nova-api'},
                {'name': 'nova-conductor'},
                {'name': 'keystone-wsgi-public'},
                {'name': 'keystone-wsgi-admin'},
                {'name': 'neutron-server'},
                {'name': 'neutron-linuxbridge-agent'},
                {'name': 'neutron-l3-agent'},
                {'name': 'neutron-dhcp-agent'},
                {'name': 'neutron-metering-agent'},
                {'name': 'neutron-metadata-agent'},
                {'name': 'neutron-ns-metadata-proxy'},
                {'name': 'glance-registry'},
                {'name': 'glance-api'},
                {'name': 'heat-api'},
                {'name': 'heat-api-cloudwatch'},
                {'name': 'heat-api-cfn'},
                {'name': 'heat-engine'},
                {'name': 'cinder-api'},
                {'name': 'cinder-scheduler'},
            ],
            # storage
            '5708c51f-5421-4ecd-9a9e-000000000003': [
                {'name': 'cinder-volume'},
            ],
        }

        self.dbapi.get_hosts_by_cluster.return_value = hosts
        self.dbapi.get_services_by_host = lambda host: services[host]

        self.engine.start()

        self.engine.driver.pre_upgrade.assert_called_once_with()
        self.assertEqual([
            # controller
            mock.call({'name': 'keystone-wsgi-admin'}, [hosts[1]]),
            mock.call({'name': 'keystone-wsgi-public'}, [hosts[1]]),
            mock.call({'name': 'glance-api'}, [hosts[1]]),
            mock.call({'name': 'glance-registry'}, [hosts[1]]),
            mock.call({'name': 'nova-conductor'}, [hosts[1]]),
            mock.call({'name': 'nova-scheduler'}, [hosts[1]]),
            mock.call({'name': 'nova-spicehtml5proxy'}, [hosts[1]]),
            mock.call({'name': 'nova-api'}, [hosts[1]]),
            mock.call({'name': 'neutron-server'}, [hosts[1]]),
            mock.call({'name': 'neutron-linuxbridge-agent'}, [hosts[1]]),
            mock.call({'name': 'neutron-l3-agent'}, [hosts[1]]),
            mock.call({'name': 'neutron-dhcp-agent'}, [hosts[1]]),
            mock.call({'name': 'neutron-metering-agent'}, [hosts[1]]),
            mock.call({'name': 'neutron-metadata-agent'}, [hosts[1]]),
            mock.call({'name': 'neutron-ns-metadata-proxy'}, [hosts[1]]),
            mock.call({'name': 'cinder-api'}, [hosts[1]]),
            mock.call({'name': 'cinder-scheduler'}, [hosts[1]]),
            mock.call({'name': 'heat-api'}, [hosts[1]]),
            mock.call({'name': 'heat-engine'}, [hosts[1]]),
            mock.call({'name': 'heat-api-cfn'}, [hosts[1]]),
            mock.call({'name': 'heat-api-cloudwatch'}, [hosts[1]]),
            # compute
            mock.call({'name': 'nova-compute'}, [hosts[0]]),
            mock.call({'name': 'neutron-linuxbridge-agent'}, [hosts[0]]),
            # storage
            mock.call({'name': 'cinder-volume'}, [hosts[2]]),
        ], self.engine.driver.start.call_args_list)

    def test_all_in_one_assignment(self):
        hosts = [
            {'id': '5708c51f-5421-4ecd-9a9e-000000000001',
             'hostname': 'host-1',
             'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687'},
        ]
        services = {
            '5708c51f-5421-4ecd-9a9e-000000000001': [
                {'name': 'nova-spicehtml5proxy'},
                {'name': 'nova-scheduler'},
                {'name': 'nova-api'},
                {'name': 'nova-conductor'},
                {'name': 'nova-compute'},
                {'name': 'keystone-wsgi-public'},
                {'name': 'keystone-wsgi-admin'},
                {'name': 'neutron-server'},
                {'name': 'neutron-linuxbridge-agent'},
                {'name': 'neutron-l3-agent'},
                {'name': 'neutron-dhcp-agent'},
                {'name': 'neutron-metering-agent'},
                {'name': 'neutron-metadata-agent'},
                {'name': 'neutron-ns-metadata-proxy'},
                {'name': 'glance-registry'},
                {'name': 'glance-api'},
                {'name': 'heat-api'},
                {'name': 'heat-api-cloudwatch'},
                {'name': 'heat-api-cfn'},
                {'name': 'heat-engine'},
                {'name': 'cinder-api'},
                {'name': 'cinder-scheduler'},
                {'name': 'cinder-volume'},
            ],
        }

        self.dbapi.get_hosts_by_cluster.return_value = hosts
        self.dbapi.get_services_by_host = lambda host: services[host]

        self.engine.start()

        self.engine.driver.pre_upgrade.assert_called_once_with()
        self.assertEqual([
            mock.call({'name': 'keystone-wsgi-admin'}, [hosts[0]]),
            mock.call({'name': 'keystone-wsgi-public'}, [hosts[0]]),
            mock.call({'name': 'glance-api'}, [hosts[0]]),
            mock.call({'name': 'glance-registry'}, [hosts[0]]),
            mock.call({'name': 'nova-conductor'}, [hosts[0]]),
            mock.call({'name': 'nova-scheduler'}, [hosts[0]]),
            mock.call({'name': 'nova-spicehtml5proxy'}, [hosts[0]]),
            mock.call({'name': 'nova-api'}, [hosts[0]]),
            mock.call({'name': 'nova-compute'}, [hosts[0]]),
            mock.call({'name': 'neutron-server'}, [hosts[0]]),
            mock.call({'name': 'neutron-linuxbridge-agent'}, [hosts[0]]),
            mock.call({'name': 'neutron-l3-agent'}, [hosts[0]]),
            mock.call({'name': 'neutron-dhcp-agent'}, [hosts[0]]),
            mock.call({'name': 'neutron-metering-agent'}, [hosts[0]]),
            mock.call({'name': 'neutron-metadata-agent'}, [hosts[0]]),
            mock.call({'name': 'neutron-ns-metadata-proxy'}, [hosts[0]]),
            mock.call({'name': 'cinder-api'}, [hosts[0]]),
            mock.call({'name': 'cinder-scheduler'}, [hosts[0]]),
            mock.call({'name': 'cinder-volume'}, [hosts[0]]),
            mock.call({'name': 'heat-api'}, [hosts[0]]),
            mock.call({'name': 'heat-engine'}, [hosts[0]]),
            mock.call({'name': 'heat-api-cfn'}, [hosts[0]]),
            mock.call({'name': 'heat-api-cloudwatch'}, [hosts[0]]),
        ], self.engine.driver.start.call_args_list)
