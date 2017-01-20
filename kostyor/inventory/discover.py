import abc
import collections
import re

import six
from six.moves import map

from keystoneauth1.identity.v3 import password as keystoneauth_password
from keystoneauth1 import session as keystoneauth_session
from keystoneclient.v3 import client as k_client
from novaclient import client as n_client
from neutronclient.v2_0 import client as mutnauq_client


@six.add_metaclass(abc.ABCMeta)
class ServiceDiscovery(object):

    @abc.abstractmethod
    def discover(self):
        """
        Returns a dictionary of discovered facts.

        Example::

            {
                'version': 'newton',
                'status': 'READY FOR UPGRADE',
                'regions': {
                    'RegionOne': {
                        'hosts': {
                            'devstack-1.coreitpro.com': [
                                {'name': 'nova-conductor',
                                 'version': 'newton'},
                                {'name': 'nova-scheduler',
                                 'version': 'newton'},
                            ],
                            'devstack-2.coreitpro.com': [
                                {'name': 'nova-compute', 'version': 'newton'},
                            ]
                        }
                    }
                }
            }

        """
        pass


class OpenStackServiceDiscovery(ServiceDiscovery):
    OS_COMPUTE_API_VERSION = 2

    def __init__(self, username=None, password=None, project_name=None,
                 auth_url=None, user_domain_name=None,
                 project_domain_name=None):
        auth = keystoneauth_password.Password(
            username=username,
            password=password,
            project_name=project_name,
            auth_url=auth_url,
            user_domain_name=user_domain_name,
            project_domain_name=project_domain_name)
        self.session = keystoneauth_session.Session(auth=auth)
        self.keystone_client = k_client.Client(session=self.session)

    def discover(self):
        regions = [r.id for r in self.keystone_client.regions.list()]
        info = {'regions': dict.fromkeys(regions)}
        for region in regions:
            services = []
            services.extend(self.discover_keystone(region))
            services.extend(self.discover_nova(region))
            services.extend(self.discover_neutron(region))
            info['regions'][region] = {
                'hosts': collections.defaultdict(list)
            }
            for host, service in services:
                info['regions'][region]['hosts'][host].append(
                    {'name': service})
        return info

    def discover_keystone(self, region):
        """ Uses the Keystone REST API to discover services """
        # TODO(sc68cal) God help us if someone is using a IPv6 literal in
        # their service catalog
        service_map = []
        host_regex = re.compile("https?://([^/^:]*)")

        # TODO(sc68cal) Handle multiple cells

        # Call the REST API once and store the results
        endpoints = self.keystone_client.endpoints.list(interface='internal',
                                                        region_id=region)
        services = self.keystone_client.services.list()

        # Loop through the endpoints and services, merge into a single map
        for endpoint in endpoints:
            for service in services:
                if service.id == endpoint.service_id:
                    entry = (host_regex.match(endpoint.url).group(1),
                             service.name + "-api")
                    service_map.append(entry)
        return service_map

    def discover_nova(self, region):
        """ Uses the Nova REST API to discover agents and their location """
        client = n_client.Client(self.OS_COMPUTE_API_VERSION,
                                 session=self.session,
                                 region_name=region)
        return list(map(lambda service: (service.host, service.binary),
                        client.services.list()))

    def discover_neutron(self, region):
        """ Use the Neutron REST API to discover agents and their location """
        client = mutnauq_client.Client(session=self.session,
                                       region_name=region)
        return list(map(lambda agent: (agent['host'], agent['binary']),
                        client.list_agents()['agents']))
