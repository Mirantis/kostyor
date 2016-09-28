import unittest

from kostyor.db import models
from kostyor.core import engine
from kostyor.core.driver import Driver


class EngineTest(unittest.TestCase):
    def test_engine(self):
        result = []

        class TestDriver(Driver):
            def get_steps(self):
                return ["step1", "step2"]

            def run_step(self, step_data):
                result.append(self.options["prefix"] + step_data)

        engine.DRIVERS["test_driver"] = TestDriver
        u_task = models.UpgradeTask()
        u_task.cluster_id = "foo"
        u_task.driver_type = "test_driver"
        u_task.driver_config = '{"prefix": "bar_"}'

        engine.start_upgrade(u_task)
        runningUpgrade = engine.RUNNING_UPGRADES.get('foo', None)
        if runningUpgrade:
            runningUpgrade.thread.join()

        self.assertEqual(["bar_step1", "bar_step2"], result)
