import cerberus
import six
import stevedore

from flask import request
from flask_restful import Resource, fields, marshal_with, abort

from kostyor.common import constants, exceptions
from kostyor.db import api as db_api


_PUBLIC_ATTRIBUTES = {
    'id': fields.String,
    'cluster_id': fields.String,
    'from_version': fields.String,
    'to_version': fields.String,
    'status': fields.String,
    'upgrade_start_time': fields.DateTime('iso8601'),
    'upgrade_end_time': fields.DateTime('iso8601'),
}


_SUPPORTED_ENGINES = stevedore.extension.ExtensionManager(
    namespace='kostyor.engines',
    invoke_on_load=False,
)


_SUPPORTED_DRIVERS = stevedore.extension.ExtensionManager(
    namespace='kostyor.upgrades.drivers',
    invoke_on_load=False,
)


class Upgrades(Resource):

    _schema = {
        'cluster_id': {
            'type': 'string',
            'required': True,
        },
        'to_version': {
            'type': 'string',
            'required': True,
            'allowed': constants.OPENSTACK_VERSIONS,
        },
        'engine': {
            'type': 'string',
            'allowed': _SUPPORTED_ENGINES.names(),
        },
        'driver': {
            'type': 'string',
            'allowed': _SUPPORTED_DRIVERS.names(),
        },
        'parameters': {
            'type': 'dict',
        },
    }

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self):
        return db_api.get_upgrades()

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def post(self):
        payload = request.get_json()

        validator = cerberus.Validator(self._schema)
        if not validator.validate(payload):
            abort(400,
                  message='Cannot create an upgrade task, passed data are '
                          'incorrect. See "errors" attribute for details.',
                  errors=validator.errors)

        try:
            upgrade = db_api.create_cluster_upgrade(
                payload['cluster_id'],
                payload['to_version']
            )

            driver_name = payload.get('driver', 'noop')
            driver = _SUPPORTED_DRIVERS[driver_name].plugin(
                parameters=payload.get('parameters', {}),
            )

            engine_name = payload.get('engine', 'node-by-node')
            engine = _SUPPORTED_ENGINES[engine_name].plugin(upgrade, driver)
            engine.start()

        except exceptions.BadRequest as exc:
            abort(400, message=six.text_type(exc))
        except exceptions.NotFound as exc:
            abort(404, message=six.text_type(exc))

        return upgrade, 201


class Upgrade(Resource):

    _actions = {
        'pause': db_api.pause_cluster_upgrade,
        'continue': db_api.continue_cluster_upgrade,
        'cancel': db_api.cancel_cluster_upgrade,
        'rollback': db_api.rollback_cluster_upgrade,
    }

    _schema = {
        'cluster_id': {'type': 'string', 'required': True},
        'action': {'type': 'string', 'required': True,
                   'allowed': list(_actions)},
    }

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self, upgrade_id):
        upgrade = db_api.get_upgrade(upgrade_id)

        if not upgrade:
            abort(404, message='Upgrade %s not found.' % upgrade_id)

        return upgrade

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def put(self, upgrade_id):
        # FIXME: dbapi implicitly retrieves recent upgrade task. i have no
        #        idea what to do with receied upgrade_id for now. I think
        #        we should either pass it to DBAPI or use another API design.
        payload = request.get_json()

        validator = cerberus.Validator(self._schema)
        if not validator.validate(payload):
            abort(400,
                  message='Cannot update an upgrade task, passed data are '
                          'incorrect. See "errors" attribute for details.',
                  errors=validator.errors)

        fn = self._actions[payload['action']]
        try:
            # Would it better to pass upgrade_id instead?
            upgrade = fn(payload['cluster_id'])
        except exceptions.NotFound as exc:
            abort(404, message=six.text_type(exc))

        return upgrade, 200
