from celery import Celery

from kostyor.conf import CONF


def create_app(conf):
    app = Celery()
    app.autodiscover_tasks(['kostyor.rpc'])

    for option, value in conf.rpc.items():
        # celery options are upper-cased, just like in flask
        app.conf[option.upper()] = value

    return app

app = create_app(CONF)
