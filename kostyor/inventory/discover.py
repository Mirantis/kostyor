import re

from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client


class KeystoneDiscovery(object):
    """ Uses the Keystone REST API to discover services """

    def __init__(self, username, password, tenant_name, auth_url):
        sess = session.Session(auth=v2.Password(username=username,
                                                password=password,
                                                tenant_name=tenant_name,
                                                auth_url=auth_url))
        self.keystone = client.Client(session=sess)

    def discover_nova_api_host(self):
        # Determine Nova API endpoint
        nova_endpoint = self.keystone.endpoints.find(
            service_id=self.keystone.services.find(type="compute").id)

        # TODO(sc68cal) God help us if someone is using an IPv6 address in
        # their service catalog
        host_regex = re.compile("https?://(.*):\d*/v\d.?\d")
        return host_regex.match(nova_endpoint.internalurl).groups()[0]


class NovaDiscovery(object):
    """ Uses the Nova REST API to discover services """
    pass
