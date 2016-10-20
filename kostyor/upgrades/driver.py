import abc
import six

from kostyor.rpc import tasks


@six.add_metaclass(abc.ABCMeta)
class UpgradeDriver():

    @abc.abstractproperty
    def supports_upgrade_rollback(self):
        """Property used to indicate if an implementation supports rolling back
        an upgrade
        """
        pass

    def pre_host_upgrade_hook(self, upgrade_task, host):
        """Called by the decision engine before a host is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        before the host is upgraded

        :param host: a host that is scheduled to be upgraded
        :type host: a kostyor.db.models.Host instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        return tasks.noop.si()

    def pre_service_upgrade_hook(self, upgrade_task, service):
        """Called by the decision engine before a service is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        before a service is upgraded

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        return tasks.noop.si()

    def post_host_upgrade_hook(self, upgrade_task, host):
        """Called by the decision engine after a host is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        after the host is upgraded

        :param host: a host that is scheduled to be upgraded
        :type host: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        return tasks.noop.si()

    def post_service_upgrade_hook(self, upgrade_task, service):
        """Called by the decision engine after a service is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        after a service is upgraded

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        return tasks.noop.si()

    @abc.abstractmethod
    def cancel_upgrade(self, upgrade_task, service):
        """Called by the decision engine to cancel an upgrade that is in
        progress

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        pass

    @abc.abstractmethod
    def rollback_upgrade(self, upgrade_task, service):
        """Called by the decision engine to rollback a running upgrade

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        pass

    @abc.abstractmethod
    def start_upgrade(self, upgrade_task, service):
        """Called by the decision engine to start an upgrade

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        pass

    @abc.abstractmethod
    def stop_upgrade(self, upgrade_task, service):
        """Called by the decision engine to stop a running upgrade

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        pass

    @abc.abstractmethod
    def pause_upgrade(self, upgrade_task, service):
        """Called by the decision engine to pause a running upgrade

        :param service: a service that is scheduled to be upgraded
        :type service: a kostyor.db.models.Service instance as a dict

        :param upgrade_task: the upgrade task that the engine is performing
        :type upgrade_task: kostyor.db.models.UpgradeTask instance
        """
        pass


class NoOpDriver(UpgradeDriver):

    def stop_upgrade(self, upgrade_task, service):
        return tasks.noop.si()

    def start_upgrade(self, upgrade_task, service):
        return tasks.noop.si()

    def pause_upgrade(self, upgrade_task, service):
        return tasks.noop.si()

    def cancel_upgrade(self, upgrade_task, service):
        return tasks.noop.si()

    def rollback_upgrade(self, upgrade_task, service):
        return tasks.noop.si()

    def continue_upgrade(self, upgrade_task, service):
        return tasks.noop.si()

    def supports_upgrade_rollback(self):
        return False
