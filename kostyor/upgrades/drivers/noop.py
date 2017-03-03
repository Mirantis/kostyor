from kostyor.upgrades.drivers import base
from kostyor.rpc import tasks


class NoopDriver(base.UpgradeDriver):

    def start(self, service, hosts):
        return tasks.noop.si()
