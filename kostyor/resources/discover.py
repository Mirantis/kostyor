import cerberus
import stevedore

from flask import request
from flask_restful import Resource, abort, marshal_with

from kostyor.common import constants
from kostyor.db import api as dbapi
from kostyor.resources.clusters import _PUBLIC_ATTRIBUTES


_SUPPORTED_DRIVERS = stevedore.extension.ExtensionManager(
    namespace='kostyor.discovery_drivers',
    invoke_on_load=False,
)


def _create_cluster(name, info):
    """Create a cluster instance based on discovered information.

    :param name: a cluster name to be used
    :type name: str

    :param info: discovered information about the deployment
    :type info: dict
    """
    cluster = dbapi.create_cluster(
        name,
        info.get('version', constants.UNKNOWN),
        info.get('status', constants.NOT_READY_FOR_UPGRADE)
    )

    for region, hosts in info.get('regions', {'Unknown': info}).items():
        for hostname, services in hosts.get('hosts', {}).items():
            host = dbapi.create_host(hostname, cluster['id'], region)
            for service in services:
                dbapi.create_service(
                    service['name'],
                    host['id'],
                    # Let's consider that service version is the same as
                    # cluster's unless stated otherwise.
                    service.get('version', cluster['version'])
                )

    return cluster


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
        cluster = _create_cluster(payload['name'], driver.discover())

        # NOTE: Discovering may be a long-running operation, so we need to
        #       consider implementing task mechanism with result polling
        #       on client side.
        return cluster, 201
