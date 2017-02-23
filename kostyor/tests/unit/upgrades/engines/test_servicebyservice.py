import datetime

import mock
import oslotest.base

from kostyor.common import constants
from kostyor.upgrades import engines

from .common import MockUpgradeDriver


class TestServiceByServiceEngine(oslotest.base.BaseTestCase):

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

    upgrade = {
        'id': 'd174522c-95fc-4996-8dfa-0c2405a3b0c1',
        'cluster_id': '2ba8fad8-3a0f-47db-a45b-62df1d811687',
        'from_version': constants.MITAKA,
        'to_version': constants.NEWTON,
        'upgrade_start_time': datetime.datetime.utcnow(),
        'upgrade_end_time': None,
        'status': constants.READY_FOR_UPGRADE,
    }

    @classmethod
    def get_fake_get_service_with_hosts(cls, assignment):
        def get_service_with_hosts(service_name, cluster_id):
            service = None
            hosts = []

            for hostid, services in assignment.items():
                try:
                    tmp_service = next(
                        svc for svc in services if svc['name'] == service_name)
                except StopIteration:
                    continue
                else:
                    service = tmp_service
                    hosts.append(hostid)

            return service, list(filter(lambda h: h['id'] in hosts, cls.hosts))
        return get_service_with_hosts

    def setUp(self):
        super(TestServiceByServiceEngine, self).setUp()
        self.engine = engines.ServiceByService(
            self.upgrade, MockUpgradeDriver()
        )

        patcher = mock.patch('kostyor.upgrades.engines.servicebyservice.dbapi')
        self.addCleanup(patcher.stop)
        self.dbapi = patcher.start()

    def test_multinode_assignment(self):
        assignment = {
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

        self.dbapi.get_service_with_hosts = \
            self.get_fake_get_service_with_hosts(assignment)

        self.engine.start()

        self.engine.driver.pre_upgrade.assert_called_once_with()
        self.assertEqual([
            mock.call({'name': 'keystone-wsgi-admin'}, [self.hosts[1]]),
            mock.call({'name': 'keystone-wsgi-public'}, [self.hosts[1]]),
            mock.call({'name': 'glance-api'}, [self.hosts[1]]),
            mock.call({'name': 'glance-registry'}, [self.hosts[1]]),
            mock.call({'name': 'nova-conductor'}, [self.hosts[1]]),
            mock.call({'name': 'nova-scheduler'}, [self.hosts[1]]),
            mock.call({'name': 'nova-spicehtml5proxy'}, [self.hosts[1]]),
            mock.call({'name': 'nova-api'}, [self.hosts[1]]),
            mock.call({'name': 'nova-compute'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-server'}, [self.hosts[1]]),
            mock.call({'name': 'neutron-linuxbridge-agent'},
                      [self.hosts[0], self.hosts[1]]),
            mock.call({'name': 'neutron-l3-agent'}, [self.hosts[1]]),
            mock.call({'name': 'neutron-dhcp-agent'}, [self.hosts[1]]),
            mock.call({'name': 'neutron-metering-agent'}, [self.hosts[1]]),
            mock.call({'name': 'neutron-metadata-agent'}, [self.hosts[1]]),
            mock.call({'name': 'neutron-ns-metadata-proxy'}, [self.hosts[1]]),
            mock.call({'name': 'cinder-api'}, [self.hosts[1]]),
            mock.call({'name': 'cinder-scheduler'}, [self.hosts[1]]),
            mock.call({'name': 'cinder-volume'}, [self.hosts[2]]),
            mock.call({'name': 'heat-api'}, [self.hosts[1]]),
            mock.call({'name': 'heat-engine'}, [self.hosts[1]]),
            mock.call({'name': 'heat-api-cfn'}, [self.hosts[1]]),
            mock.call({'name': 'heat-api-cloudwatch'}, [self.hosts[1]]),
        ], self.engine.driver.start.call_args_list)

    def test_all_in_one_assignment(self):
        assignment = {
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

        self.dbapi.get_service_with_hosts = \
            self.get_fake_get_service_with_hosts(assignment)

        self.engine.start()

        self.engine.driver.pre_upgrade.assert_called_once_with()
        self.assertEqual([
            mock.call({'name': 'keystone-wsgi-admin'}, [self.hosts[0]]),
            mock.call({'name': 'keystone-wsgi-public'}, [self.hosts[0]]),
            mock.call({'name': 'glance-api'}, [self.hosts[0]]),
            mock.call({'name': 'glance-registry'}, [self.hosts[0]]),
            mock.call({'name': 'nova-conductor'}, [self.hosts[0]]),
            mock.call({'name': 'nova-scheduler'}, [self.hosts[0]]),
            mock.call({'name': 'nova-spicehtml5proxy'}, [self.hosts[0]]),
            mock.call({'name': 'nova-api'}, [self.hosts[0]]),
            mock.call({'name': 'nova-compute'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-server'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-linuxbridge-agent'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-l3-agent'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-dhcp-agent'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-metering-agent'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-metadata-agent'}, [self.hosts[0]]),
            mock.call({'name': 'neutron-ns-metadata-proxy'}, [self.hosts[0]]),
            mock.call({'name': 'cinder-api'}, [self.hosts[0]]),
            mock.call({'name': 'cinder-scheduler'}, [self.hosts[0]]),
            mock.call({'name': 'cinder-volume'}, [self.hosts[0]]),
            mock.call({'name': 'heat-api'}, [self.hosts[0]]),
            mock.call({'name': 'heat-engine'}, [self.hosts[0]]),
            mock.call({'name': 'heat-api-cfn'}, [self.hosts[0]]),
            mock.call({'name': 'heat-api-cloudwatch'}, [self.hosts[0]]),
        ], self.engine.driver.start.call_args_list)
