import cerberus
import stevedore

from flask import request
from flask_restful import Resource, abort, marshal_with

from kostyor.db import api as dbapi
from kostyor.resources.clusters import _PUBLIC_ATTRIBUTES


_SUPPORTED_DRIVERS = stevedore.extension.ExtensionManager(
    namespace='kostyor.discovery_drivers',
    invoke_on_load=False,
)


class Discover(Resource):

    _schema = {
        'name': {
            'type': 'string',
            'required': True,
        },
        'method': {
            'type': 'string',
            'required': True,
            'allowed': _SUPPORTED_DRIVERS.names(),
        },
        'parameters': {
            'type': 'dict',
        },
    }

    def get(self):
        return _SUPPORTED_DRIVERS.names()

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def post(self):
        payload = request.get_json()

        validator = cerberus.Validator(self._schema)
        if not validator.validate(payload):
            abort(400,
                  message='Cannot discover a cluster, passed data are '
                          'incorrect. See "errors" attribute for details.',
                  errors=validator.errors)

        DriverCls = _SUPPORTED_DRIVERS[payload['method']].plugin
        driver = DriverCls(**payload.get('parameters', {}))
        cluster = dbapi.discover_cluster(payload['name'], driver.discover())

        # NOTE: Discovering may be a long-running operation, so we need to
        #       consider implementing task mechanism with result polling
        #       on client side.
        return cluster, 201
