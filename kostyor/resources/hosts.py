import six

from flask_restful import Resource, fields, marshal_with, abort

from kostyor.common import exceptions
from kostyor.db import api as db_api


# Output Schema is a Flask-RESTful marshaling schema that's used to
# expose only limited set of fields and to do type transformation.
_PUBLIC_ATTRIBUTES = {
    'id': fields.String,
    'hostname': fields.String,
    'cluster_id': fields.String,
}


class Hosts(Resource):

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self, cluster_id):
        try:
            hosts = db_api.get_hosts_by_cluster(cluster_id)
        except exceptions.NotFound as exc:
            abort(404, message=six.text_type(exc))

        return hosts
