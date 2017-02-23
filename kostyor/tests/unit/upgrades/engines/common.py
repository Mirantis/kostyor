import mock

from kostyor.rpc import tasks
from kostyor.upgrades.drivers import base as basedriver


class MockUpgradeDriver(basedriver.UpgradeDriver):
    """Special driver implementation to track calls to its methods."""

    _methods = [
        'pre_upgrade',
        'start',
    ]

    def __new__(cls):
        # Since we don't implement abstract methods but mock them instead,
        # we need to consider everything implemented and do not fail on
        # attempt to create an instance.
        cls.__abstractmethods__ = set()

        instance = super(MockUpgradeDriver, cls).__new__(cls)
        for method in cls._methods:
            setattr(instance, method, mock.Mock(return_value=tasks.noop.si()))
        return instance
