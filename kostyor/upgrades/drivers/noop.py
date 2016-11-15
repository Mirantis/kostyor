from kostyor.upgrades.drivers import base
from kostyor.rpc import tasks


class NoOpDriver(base.UpgradeDriver):

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
