import abc
import six


@six.add_metaclass(abc.ABCMeta)
class UpgradeDriver():

    @abc.abstractproperty
    def supports_upgrade_rollback(self):
        """Property used to indicate if an implementation supports rolling back
        an upgrade
        """
        pass

    @abc.abstractmethod
    def pre_host_upgrade_hook(self, host):
        """Called by the decision engine before a host is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        before the host is upgraded

        Params

        host: a kostyor.db.models.Host instance, representing the host that is
        scheduled to be upgraded
        """
        pass

    @abc.abstractmethod
    def pre_service_upgrade_hook(self, service):
        """Called by the decision engine before a service is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        before a service is upgraded

        Params

        service: a kostyor.db.models.Service instance, representing the service
        that is scheduled to be upgraded
        """
        pass

    @abc.abstractmethod
    def post_host_upgrade_hook(self, host):
        """Called by the decision engine after a host is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        after the host is upgraded

        Params

        host: a kostyor.db.models.Host instance, representing the host that is
        scheduled to be upgraded
        """
        pass

    @abc.abstractmethod
    def post_service_upgrade_hook(self, service):
        """Called by the decision engine after a service is upgraded,
        allows an UpgradeDriver the opportunity to do any operations required
        after a service is upgraded

        Params

        service: a kostyor.db.models.Service instance, representing the service
        that is scheduled to be upgraded
        """
        pass

    @abc.abstractmethod
    def cancel_upgrade(self):
        pass

    @abc.abstractmethod
    def rollback_upgrade(self):
        pass

    @abc.abstractmethod
    def start_upgrade(self):
        pass

    @abc.abstractmethod
    def stop_upgrade(self):
        pass

    @abc.abstractmethod
    def pause_upgrade(self):
        pass
