import mock
import unittest

from kostyor.inventory import discover


class OpenStackServiceDiscoveryTest(unittest.TestCase):

    def setUp(self):
        keystone = mock.Mock()
        self.osd = discover.OpenStackServiceDiscovery(keystone)

    @mock.patch('novaclient.v2.services.ServiceManager.list')
    def test_discover_nova(self, fake_manager_list):
        expected = [
            {'host': 'foo', 'name': 'nova-cpu', 'region': 'RegionOne'},
            {'host': 'bar', 'name': 'nova-cpu', 'region': 'RegionOne'},
        ]
        service1 = mock.Mock()
        service1.host = "foo"
        service1.binary = 'nova-cpu'
        service2 = mock.Mock()
        service2.host = "bar"
        service2.binary = 'nova-cpu'
        fake_manager_list.return_value = [service1, service2]
        res = self.osd.discover_nova('RegionOne')
        self.assertEqual(expected, res)

    @mock.patch("neutronclient.v2_0.client.Client.list_agents")
    def test_discover_neutron(self, fake_list_agents):
        expected = [{'host': 'foo',
                     'name': 'neutron-l3',
                     'region': 'RegionOne'}, ]
        fake_list_agents.return_value = {"agents": [{"binary": "neutron-l3",
                                                     "host": "foo"}]}
        res = self.osd.discover_neutron('RegionOne')
        self.assertEqual(expected, res)

    @mock.patch("keystoneclient.v2_0.endpoints.EndpointManager.list")
    @mock.patch("keystoneclient.v2_0.services.ServiceManager.list")
    def test_discover_keystone(self, fk_servicemanager, fk_endpointmanager):
        host = 'http://devstack-1.coreitpro.com:93923/'
        fake_id = 'fake-id'
        expected = [{'host': 'devstack-1.coreitpro.com',
                     'name': 'nova-api',
                     'region': 'RegionOne'}, ]
        fake_endpoint = mock.Mock()
        fake_endpoint.service_id = fake_id
        fake_endpoint.internalurl = host
        fake_endpoint.region = 'RegionOne'
        fake_service = mock.Mock()
        fake_service.id = fake_id
        fake_service.name = 'nova'

        fk_endpointmanager.return_value = [fake_endpoint]
        fk_servicemanager.return_value = [fake_service]
        self.assertEqual(expected, self.osd.discover_keystone())

    @mock.patch.object(discover.OpenStackServiceDiscovery, 'discover_keystone')
    @mock.patch.object(discover.OpenStackServiceDiscovery, 'discover_nova')
    @mock.patch.object(discover.OpenStackServiceDiscovery, 'discover_neutron')
    def test_discover(self, fake_discover_neutron, fake_discover_nova,
                      fake_discover_keystone):
        def _discover_neutron(region):
            return [{'region': region,
                     'host': region + '_host',
                     'name': 'neutron-agent'}, ]

        def _discover_nova(region):
            return [{'region': region,
                     'host': region + '_host',
                     'name': 'nova-scheduler'}, ]

        fake_discover_neutron.side_effect = _discover_neutron
        fake_discover_nova.side_effect = _discover_nova
        fake_discover_keystone.return_value = [
            {'host': 'region_one_host',
             'name': 'nova-api',
             'region': 'region_one'},
            {'host': 'region_two_host',
             'name': 'nova-api',
             'region': 'region_two'},
        ]

        expected_mock_calls = [mock.call('region_one'),
                               mock.call('region_two')]

        info = self.osd.discover()['regions']

        fake_discover_neutron.assert_has_calls(expected_mock_calls,
                                               any_order=True)
        fake_discover_nova.assert_has_calls(expected_mock_calls,
                                            any_order=True)
        fake_discover_keystone.assert_called_once_with()

        for region in ['region_one', 'region_two']:
            self.assertIn(region, info)
            hosts = info[region]['hosts']
            self.assertIn(region + '_host', hosts)
            self.assertEqual(1, len(hosts))
            self.assertEqual([{'name': 'nova-api'},
                              {'name': 'nova-scheduler'},
                              {'name': 'neutron-agent'}, ],
                             hosts[region+'_host'])
