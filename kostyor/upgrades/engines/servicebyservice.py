import celery

from kostyor.db import api as dbapi
from .nodebynode import SCENARIO


class ServiceByService(object):
    """Manage a service-by-service upgrade of OpenStack environment.

    This includes but not limited to the following steps:

      - Determine a sequence of steps to take for the requested action.
      - Form a sequence of tasks to be sent to task broker.

    See OpenStack OPS upgrades guide for details on upgrade order:

        http://docs.openstack.org/ops-guide/ops-upgrades.html

    :param upgrade: an upgrade task to proceed with
    """

    def __init__(self, upgrade, driver):
        self._upgrade = upgrade
        self.driver = driver

    def start(self):
        subtasks = [self.driver.pre_upgrade()]

        for project in SCENARIO:
            for service in project.services:
                service, hosts = dbapi.get_service_with_hosts(
                    service.name,
                    self._upgrade['cluster_id'])

                # SCENARIO may contain services that are not deployed in
                # current setup. Hence, attempt to return its instance
                # and hosts will return None, and we have no choice but
                # ignore it and continue.
                if service:
                    subtasks.append(self.driver.start(service, hosts))

        # Execute gathered tasks one-by-one preserving order. Please note,
        # that it doesn't mean there can't be parallel execution since driver
        # may return a Celery group of tasks instead, and in that case the
        # group will be executed instead. The idea is to run one-by-one what
        # was returned by driver regardless whether it's a task, a group or
        # a chain.
        supertask = celery.chain(*subtasks)
        supertask.apply_async()
