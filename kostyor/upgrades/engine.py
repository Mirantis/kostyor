import collections

import celery

from kostyor.db import api as dbapi
from kostyor.upgrades import driver as upgrade_driver


Project = collections.namedtuple('Project', ['name', 'services'])
Service = collections.namedtuple('Service', ['name', 'tags'])


# OpenStack Rolling Upgrade Scenario
#
# Overall this is a huge scenario for OpenStack rolling upgrades. The OpenStack
# services will be upgraded project-by-project in the order specified here.
SCENARIO = [
    Project('Keystone', [
        Service('keystone-wsgi-admin',  ['controller']),
        Service('keystone-wsgi-public', ['controller']),
    ]),

    Project('Glance', [
        Service('glance-api',      ['controller']),
        Service('glance-registry', ['controller']),
    ]),

    Project('Nova', [
        Service('nova-conductor',       ['controller']),
        Service('nova-scheduler',       ['controller']),
        Service('nova-cells',           ['controller']),
        Service('nova-cert',            ['controller']),
        Service('nova-console',         ['controller']),
        Service('nova-consoleauth',     ['controller']),
        Service('nova-network',         ['controller']),
        Service('nova-novncproxy',      ['controller']),
        Service('nova-serialproxy',     ['controller']),
        Service('nova-spicehtml5proxy', ['controller']),
        Service('nova-xvpvncproxy',     ['controller']),
        Service('nova-api',             ['controller']),
        Service('nova-api-metadata',    ['controller']),
        Service('nova-api-os-compute',  ['controller']),
        Service('nova-compute',         ['compute']),
    ]),

    Project('Neutron', [
        Service('neutron-server',            ['controller']),
        Service('neutron-openvswitch-agent', ['controller', 'compute']),
        Service('neutron-linuxbridge-agent', ['controller', 'compute']),
        Service('neutron-sriov-nic-agent',   ['controller', 'compute']),
        Service('neutron-l3-agent',          ['controller']),
        Service('neutron-dhcp-agent',        ['controller']),
        Service('neutron-metering-agent',    ['controller']),
        Service('neutron-metadata-agent',    ['controller']),
        Service('neutron-ns-metadata-proxy', ['controller']),
    ]),

    Project('Cinder', [
        Service('cinder-api',       ['controller']),
        Service('cinder-scheduler', ['controller']),
        Service('cinder-volume',    ['storage']),
    ]),

    Project('Heat', [
        Service('heat-api',            ['controller']),
        Service('heat-engine',         ['controller']),
        Service('heat-api-cfn',        ['controller']),
        Service('heat-api-cloudwatch', ['controller']),
    ]),
]


def _get_hosts_by_tag(hosts, tag):
    serviceindex = [
        service.name
        for project in SCENARIO for service in project.services
        if tag in service.tags
    ]

    def _interested(host):
        return next((
            svc['name'] in serviceindex
            for svc in dbapi.get_services_by_host(host['id'])
        ), None)
    tagged_hosts = filter(_interested, hosts)

    def _sortkey(host):
        services = dbapi.get_services_by_host(host['id'])

        # Well, that's a tricky part. :) We need to sort hosts in the order
        # of service occurrence. Since each host may (and probably will)
        # contain multiple services, we need to use the most important
        # one as a sort key.
        return min((serviceindex.index(svc['name']) for svc in services))
    return sorted(tagged_hosts, key=_sortkey)


def get_controllers(hosts):
    return _get_hosts_by_tag(hosts, 'controller')


def get_computes(hosts):
    return _get_hosts_by_tag(hosts, 'compute')


def get_storages(hosts):
    return _get_hosts_by_tag(hosts, 'storage')


def iterservices(host):
    serviceindex = [
        service.name
        for project in SCENARIO for service in project.services
    ]

    servicemap = {
        service['name']: service
        for service in dbapi.get_services_by_host(host['id'])
    }

    # In order to ensure proper order we need to iterate over the service
    # index in the order specified in SCENARIO.
    for service in serviceindex:
        if service in servicemap:
            yield servicemap[service]


class Engine(object):
    """Manage a node-by-node rolling upgrade of OpenStack environment.

    This includes but not limited to the following steps:

      - Determine a sequence of steps to take for the requested action.
      - Form a sequence of tasks to be sent to task broker.

    See OpenStack OPS upgrades guide for details on upgrade order:

        http://docs.openstack.org/ops-guide/ops-upgrades.html

    :param upgrade: an upgrade task to proceed with
    """

    def __init__(self, upgrade, driver=upgrade_driver.NoOpDriver()):
        self._upgrade = upgrade
        self.driver = driver

    def start(self):
        subtasks = []
        hosts = dbapi.get_hosts_by_cluster(self._upgrade['cluster_id'])

        # We may have plenty controllers each with various set of services.
        # In order to orchestrate upgrades properly, we need to iterate
        # by them in right order. For example, first goes controllers with
        # keystone, then with nova, and so on. See iteration details in
        # get_controllers() docstring.
        for host in get_controllers(hosts):
            self.driver.pre_host_upgrade_hook(host)
            for service in iterservices(host):
                self.driver.pre_service_upgrade_hook(service)
                subtasks.append(self.driver.start_upgrade(service))

        # Well, controllers are done. It's time to upgrade compute nodes.
        # Again, node by node, service by service.
        for host in get_computes(hosts):
            self.driver.pre_host_upgrade_hook(host)
            for service in iterservices(host):
                subtasks.append(self.driver.start_upgrade(service))

        # Finishing upgrades by upgrading storage nodes.
        for host in get_storages(hosts):
            self.driver.pre_host_upgrade_hook(host)
            for service in iterservices(host):
                subtasks.append(self.driver.start_upgrade(service))

        # Execute gathered tasks one-by-one preserving order. Please note,
        # that it doesn't mean there can't be parallel execution since driver
        # may return a Celery group of tasks instead, and in that case the
        # group will be executed instead. The idea is to run one-by-one what
        # was returned by driver regardless whether it's a task, a group or
        # a chain.
        supertask = celery.chain(*subtasks)
        supertask.apply_async()
