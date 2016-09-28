import re
import os

from ansible.cli.playbook import PlaybookCLI
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.executor.playbook_executor import PlaybookExecutor

from kostyor.core.driver import Driver


class AnsibleDriver(Driver):
    def get_steps(self):
        playbook_path = self.options["playbook_path"]
        script_name = "%s/scripts/run-upgrade.sh" % playbook_path
        with open(script_name, 'r') as script_file:
            script = script_file.read()

        run_tasks = re.findall("^\s+RUN_TASKS\+=\(\"(.*)\"\)", script,
                               re.MULTILINE)
        steps = []
        for task in run_tasks:
            if task.startswith("$"):
                steps.append(task.replace("${UPGRADE_PLAYBOOKS}",
                                          "upgrade-utilities/playbooks"))
            else:
                steps.append(os.path.join('playbooks', task))

        steps = [os.path.join(playbook_path, x) for x in steps]
        return steps

    def run_step(self, step_data):
        args = [""]
        args.extend(step_data.split(" "))
        pb = PlaybookCLI(args)
        pb.parse()
        variable_manager = VariableManager()
        loader = DataLoader()
        inventory = Inventory(loader=loader, variable_manager=variable_manager)
        playbook_path = args[1]

        self.pbex = PlaybookExecutor(playbooks=[playbook_path],
                                     inventory=inventory,
                                     variable_manager=variable_manager,
                                     loader=loader, options=pb.options,
                                     passwords={})

        self.pbex.run()

    def stop_step(self):
        self.pbex._tqm.terminate()
