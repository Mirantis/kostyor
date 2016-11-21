import oslotest.base

from kostyor.rpc.app import app


# In order to avoid circular import dependencies, we use lazy task
# loading (see 'app.autodiscover_tasks' method). The real loading
# is triggered on a special signal that's emitted by worker. Since
# we don't have worker in unit tests, let's emit this signal
# manually.
app.loader.import_default_modules()


class TestRpcApp(oslotest.base.BaseTestCase):

    def test_default_tasks_are_loaded(self):
        expected_tasks = [
            'kostyor.rpc.tasks.noop.noop',
            'kostyor.rpc.tasks.execute.execute',
        ]

        self.assertTrue(set(expected_tasks).issubset(app.tasks))
