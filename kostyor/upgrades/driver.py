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

    def pre_host_upgrade_hook(self, host):
        """Called by the decision engine before a host is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        before the host is upgraded

        Params

        host: a kostyor.db.models.Host instance, representing the host that is
        scheduled to be upgraded
        """
        return tasks.noop.si()

    def pre_service_upgrade_hook(self, service):
        """Called by the decision engine before a service is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        before a service is upgraded

        Params

        service: a kostyor.db.models.Service instance, representing the service
        that is scheduled to be upgraded
        """
        return tasks.noop.si()

    def post_host_upgrade_hook(self, host):
        """Called by the decision engine after a host is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        after the host is upgraded

        Params

        host: a kostyor.db.models.Host instance, representing the host that is
        scheduled to be upgraded
        """
        return tasks.noop.si()

    def post_service_upgrade_hook(self, service):
        """Called by the decision engine after a service is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        after a service is upgraded

        Params

        service: a kostyor.db.models.Service instance, representing the service
        that is scheduled to be upgraded
        """
        return tasks.noop.si()

    @abc.abstractmethod
    def cancel_upgrade(self, upgrade_task):
        """Called by the decision engine to cancel an upgrade that is in
        progress"""
        pass

    @abc.abstractmethod
    def rollback_upgrade(self, upgrade_task):
        """Called by the decision engine to rollback a running upgrade

        Params

        upgrade_task: A kostyor.db.models.UpgradeTask instance"""
        pass

    @abc.abstractmethod
    def start_upgrade(self, upgrade_task):
        """Called by the decision engine to start an upgrade

        Params

        upgrade_task: A kostyor.db.models.UpgradeTask instance"""
        pass

    @abc.abstractmethod
    def stop_upgrade(self, upgrade_task):
        """Called by the decision engine to stop a running upgrade

        Params

        upgrade_task: A kostyor.db.models.UpgradeTask instance"""
        pass

    @abc.abstractmethod
    def pause_upgrade(self, upgrade_task):
        """Called by the decision engine to pause a running upgrade

        Params

        upgrade_task: A kostyor.db.models.UpgradeTask instance"""
        pass


class FakeUpgradeDriver(UpgradeDriver):

    def stop_upgrade(self, upgrade_task):
        return tasks.noop.si()

    def start_upgrade(self, upgrade_task):
        return tasks.noop.si()

    def pause_upgrade(self, upgrade_task):
        return tasks.noop.si()

    def cancel_upgrade(self, upgrade_task):
        return tasks.noop.si()

    def rollback_upgrade(self, upgrade_task):
        return tasks.noop.si()

    def continue_upgrade(self, upgrade_task):
        return tasks.noop.si()

    def supports_upgrade_rollback(self):
        return False
