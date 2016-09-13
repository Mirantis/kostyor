from flask import request
from flask_restful import Resource, fields, marshal_with, abort

from kostyor.db import api as db_api


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

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self, cluster_id):
        cluster = db_api.get_cluster(cluster_id)

        if not cluster:
            abort(404, message='Cluster %s not found.' % cluster_id)

        return cluster

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def put(self, cluster_id):
        return db_api.update_cluster(cluster_id, **request.form)
