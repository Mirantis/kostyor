import collections

import celery

from kostyor.db import api as dbapi
from kostyor.upgrades.drivers import noop as noop_driver


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


def iterhosts(hosts):
    def _sortkey(service):
        for index, tag in enumerate(['controller', 'compute', 'storage']):
            if tag in service.tags:
                return index

    # Generate serviceindex where first goes services of controllers, then -
    # services of computes, and only then - ones from storages. This is an
    # essential part for getting proper an upgrade order of hosts as it's
    # used below to determine most important ones.
    serviceindex = [
        service.name
        for service in sorted(
            [service for project in SCENARIO for service in project.services],
            key=_sortkey
        )
    ]

    def _sortkey(host):
        services = dbapi.get_services_by_host(host['id'])
        # Well, that's a tricky part. :) We need to sort hosts in the order
        # of service occurrence. Since each host may (and probably will)
        # contain multiple services, we need to use the most important
        # one as a sort key.
        return min((serviceindex.index(svc['name']) for svc in services))
    return sorted(hosts, key=_sortkey)


def iterservices(host):
    serviceindex = [
        service.name for project in SCENARIO for service in project.services
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

    def __init__(self, upgrade, driver=noop_driver.NoOpDriver()):
        self._upgrade = upgrade
        self.driver = driver

    def start(self):
        subtasks = [self.driver.pre_upgrade_hook(self._upgrade)]
        hosts = dbapi.get_hosts_by_cluster(self._upgrade['cluster_id'])

        # We may have plenty controllers each with various set of services.
        # In order to orchestrate upgrades properly, we need to iterate
        # by them in right order. For example, first goes controllers with
        # keystone, then with nova, and so on. See iteration details in
        # get_controllers() docstring.
        for host in iterhosts(hosts):
            subtasks.append(
                self.driver.pre_host_upgrade_hook(self._upgrade, host)
            )

            for service in iterservices(host):
                subtasks.extend([
                    self.driver.pre_service_upgrade_hook(
                        self._upgrade, service
                    ),
                    self.driver.start_upgrade(
                        self._upgrade, service
                    ),
                    self.driver.post_service_upgrade_hook(
                        self._upgrade, service
                    ),
                ])

            subtasks.append(
                self.driver.post_host_upgrade_hook(self._upgrade, host)
            )

        # Execute gathered tasks one-by-one preserving order. Please note,
        # that it doesn't mean there can't be parallel execution since driver
        # may return a Celery group of tasks instead, and in that case the
        # group will be executed instead. The idea is to run one-by-one what
        # was returned by driver regardless whether it's a task, a group or
        # a chain.
        supertask = celery.chain(*subtasks)
        supertask.apply_async()
