import abc
import six


@six.add_metaclass(abc.ABCMeta)
class DefaultStrategy():
    pass


@six.add_metaclass(abc.ABCMeta)
class HostEvacuateLiveMixin():
    """

    A strategy that includes using the nova host-evacuate-live API call
    to live-migrate running instances off a compute node

    http://www.danplanet.com/blog/2016/03/03/evacuate-in-nova-one-command-to-confuse-us-all/
    """

    def __init__(self):
        self.host_evacuate_live = True

    def host_evacuate_live(self):
        return self.host_evacuate_live
