import abc
import six

from kostyor.rpc import tasks


@six.add_metaclass(abc.ABCMeta)
class UpgradeDriver():

    def __init__(self, parameters=None):
        self.parameters = parameters or {}

    def pre_upgrade(self):
        """Get tasks to be executed before main upgrade procedure.

        :returns: a celery signature
        """
        return tasks.noop.si()

    @abc.abstractmethod
    def start(self, service, hosts):
        """Get tasks to upgrade a given service on a give hosts.

        :param service: a service to be upgraded
        :param hosts: a list of hosts to run upgrade on
        :returns: a celery signature
        """
