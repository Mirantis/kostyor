import celery
import pkg_resources

from kostyor.conf import CONF


def create_app(conf):
    app = celery.Celery()

    for option, value in conf.rpc.items():
        # celery options are upper-cased, just like in flask
        app.conf[option.upper()] = value

    # Each driver may use own set of Celery tasks, so in order to run them
    # the Celery worker has to load them into memory. That's why we need to
    # iterate over Kostyor drivers and lazily load them into memory. The
    # important note here is that we can't use stevedore because it tries
    # to load found module immediately which leads to cyclic import error
    # (drivers import a celery app in order to define own tasks).
    for ep in pkg_resources.iter_entry_points('kostyor.upgrades.drivers'):
        package, module = ep.module_name.rsplit('.', 1)
        app.autodiscover_tasks([package], module)

    return app


app = create_app(CONF)
