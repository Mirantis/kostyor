import abc
import re


from keystoneclient.v2_0 import client as k_client
from novaclient import client as n_client
from neutronclient.v2_0 import client as mutnauq_client

OS_COMPUTE_API_VERSION = 2


@abc.ABCMeta
class ServiceDiscovery(object):

    @abc.abstractmethod
    def discover(self):
        """
        Returns a list of services, and the host they are on.

        Example:

            [(u'devstack-1.coreitpro.com', u'nova-conductor'),
             (u'devstack-1.coreitpro.com', u'nova-cert'),
             (u'devstack-1.coreitpro.com', u'nova-scheduler'),
             (u'devstack-1.coreitpro.com', u'nova-consoleauth'),
             (u'devstack-1.coreitpro.com', u'nova-compute'),
             (u'devstack-2.coreitpro.com', u'nova-compute'),
             (u'devstack-3.coreitpro.com', u'nova-compute')]
        """
        pass


class OpenStackServiceDiscovery(ServiceDiscovery):
    """
    Users of this class need to create a keystone session and pass it
    into the constructor.

    Example:
        from keystoneauth1.identity import v2
        from keystoneauth1 import session
        sess = session.Session(auth=v2.Password(username='admin',
            password='changeme', tenant_name='demo',
            auth_url="http://192.168.1.246:5000/v2.0/"))

        cluster_discovery = ServiceDiscovery(sess)
        cluster_discovery.discover()

    """
    def __init__(self, keystone_session):
        self.session = keystone_session

    def discover(self):
        services = []
        services.extend(self.discover_keystone())
        services.extend(self.discover_nova())
        services.extend(self.discover_neutron())
        return services

    def discover_keystone(self):
        """ Uses the Keystone REST API to discover services """
        # TODO(sc68cal) God help us if someone is using a IPv6 literal in
        # their service catalog
        service_map = []
        host_regex = re.compile("https?://(.*):\d*")

        self.client = k_client.Client(session=self.session)
        # TODO(sc68cal) Handle multiple regions and cells

        # Call the REST API once and store the results
        endpoints = self.client.endpoints.list()
        services = self.client.services.list()

        # Loop through the endpoints and services, merge into a single map
        for endpoint in endpoints:
            for service in services:
                if service.id == endpoint.service_id:
                    entry = (host_regex.match(endpoint.internalurl).group(1),
                             service.name + "-api")
                    service_map.append(entry)
        return service_map


    def discover_nova(self):
        """ Uses the Nova REST API to discover agents and their location """
        self.client = n_client.Client(OS_COMPUTE_API_VERSION,
                                      session=self.session)
        return map(lambda service: (service.host, service.binary),
                   self.client.services.list())


    def discover_neutron(self):
        """ Use the Neutron REST API to discover agents and their location """
        self.client = mutnauq_client.Client(session=self.session)
        return map(lambda agent: (agent['binary'], agent['host']),
                   self.client.list_agents()['agents'])
