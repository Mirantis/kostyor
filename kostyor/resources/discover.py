import collections

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
        info.get('status', constants.NOT_READY_FOR_UPGRADE),
    )

    host_services_map = collections.defaultdict(list)
    for host, service in info.get('services', []):
        host_services_map[host].append(service)

    hosts_ids = {}
    for host in host_services_map:
        hosts_ids[host] = dbapi.create_host(host, cluster['id'])['id']

    for host, service in host_services_map.items():
        for s in service:
            # Let's consider that service version is the same as cluster's
            # unless stated otherwise.
            dbapi.create_service(s, hosts_ids[host], cluster['version'])

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
        cluster = _create_cluster(payload['name'], {
            'services': driver.discover(),
        })

        # NOTE: Discovering may be a long-running operation, so we need to
        #       consider implementing task mechanism with result polling
        #       on client side.
        return cluster, 201
