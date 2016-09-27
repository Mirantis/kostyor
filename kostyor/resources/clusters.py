import cerberus

from flask import request
from flask_restful import Resource, fields, marshal_with, abort

from kostyor.common import constants
from kostyor.db import api as db_api


# Output Schema is a Flask-RESTful marshaling schema that's used to
# expose only limited set of fields and to do type transformation.
_PUBLIC_ATTRIBUTES = {
    'id': fields.String,
    'name': fields.String,
    'status': fields.String,
    'version': fields.String,
}


class Clusters(Resource):

    @marshal_with({'clusters': fields.Nested(_PUBLIC_ATTRIBUTES)})
    def get(self):
        # TODO: get rid of intermediate 'clusters' attribute
        return {'clusters': db_api.get_clusters()}


class Cluster(Resource):

    _schema = {
        'id': {'type': 'string', 'readonly': True},
        'name': {'type': 'string'},
        'status': {'type': 'string', 'allowed': constants.STATUSES},
        'version': {'type': 'string', 'allowed': constants.OPENSTACK_VERSIONS},
    }

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self, cluster_id):
        cluster = db_api.get_cluster(cluster_id)

        if not cluster:
            abort(404, message='Cluster %s not found.' % cluster_id)

        return cluster

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def put(self, cluster_id):
        validator = cerberus.Validator(self._schema)
        if not validator.validate(request.get_json()):
            abort(400,
                  message='Cannot update a cluster "%s", passed data are '
                          'incorrect. See "errors" attribute for details.'
                          % cluster_id,
                  errors=validator.errors)

        return db_api.update_cluster(cluster_id, **request.form)
