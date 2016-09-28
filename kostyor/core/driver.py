import json


class Driver(object):
    def __init__(self, options):
        self.options = json.loads(options)

    def get_steps(self):
        pass

    def run_step(self, step_data):
        pass

    def stop_step(self):
        pass
