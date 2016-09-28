import json
import os
import unittest

from kostyor.drivers.ansible_driver import AnsibleDriver


class AnsibleDriverTest(unittest.TestCase):
    def test_get_steps(self):
        ansible_playbook = os.path.join(os.path.dirname(__file__),
                                        '../../resources/ansible')

        expected = ["upgrade-utilities/playbooks/lbaas-version-check.yml",
                    "playbooks/setup-hosts.yml --limit '!galera_all'"]

        expected = [os.path.join(ansible_playbook, x) for x in expected]

        options = {"playbook_path": ansible_playbook}
        driver = AnsibleDriver(json.dumps(options))

        self.assertEqual(expected, driver.get_steps())
