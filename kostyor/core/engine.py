import threading

from kostyor.common import constants
from kostyor.drivers import ansible_driver


RUNNING_UPGRADES = {}
RUNNING_UPGRADES_LOCK = threading.Lock()

DRIVERS = {constants.ANSIBLE: ansible_driver.AnsibleDriver}


class RunningUpgrade(object):
    def __init__(self):
        self.thread = None
        self.driver = None
        self.terminated = False

    def stop(self):
        self.terminated = True
        self.driver.stop_step()


def start_upgrade(u_task):
    running_upgrade = RunningUpgrade()
    RUNNING_UPGRADES_LOCK.acquire()
    try:
        if u_task.cluster_id in RUNNING_UPGRADES:
            raise Exception("Upgrade for cluster \"%s\" is already running."
                            % u_task.cluster_id)
        RUNNING_UPGRADES[u_task.cluster_id] = running_upgrade
    finally:
        RUNNING_UPGRADES_LOCK.release()
    thread = threading.Thread(target=do_upgrade, args=(u_task,
                                                       running_upgrade))
    running_upgrade.thread = thread
    thread.start()


def do_upgrade(u_task, running_upgrade):
    try:
        driver = DRIVERS[u_task.driver_type](u_task.driver_config)
        running_upgrade.driver = driver
        steps = driver.get_steps()
        # TODO store steps in DB
        for step in steps:
            driver.run_step(step)
            if running_upgrade.terminated:
                return
            # TODO store current step successful status
    finally:
        RUNNING_UPGRADES_LOCK.acquire()
        RUNNING_UPGRADES.pop(u_task.cluster_id, None)
        RUNNING_UPGRADES_LOCK.release()


def resume_upgrade(self):
    pass


def stop_upgrade(u_task):
    RUNNING_UPGRADES[u_task.cluster_id].stop()
