import abc
import six

from kostyor.upgrade import strategy as kostyor_strategy

# Not nessesarily in order, but some of the phases
# that an upgrade can be broken into
# TODO: add more fine grained phases? subphases?
UPGRADE_PHASES = ['pre-upgrade',
                  'API services upgrade',
                  'compute resource upgrade',
                  'network resource upgrade',
                  'storage resource upgrade']


@six.add_metaclass(abc.ABCMeta)
class UpgradeOrchestrator():
    """ This abstract class defines the
    methods that are called during an orchestrated upgrade.

    """

    @abc.abstractproperty
    def strategy(self):
        return self.strategy

    def __init__(self, strategy=kostyor_strategy.DefaultStrategy):
        self.strategy = strategy
