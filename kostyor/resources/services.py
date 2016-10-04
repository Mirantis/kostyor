import six

from flask_restful import Resource, fields, marshal_with, abort

from kostyor.common import exceptions
from kostyor.db import api as db_api


# Output Schema is a Flask-RESTful marshaling schema that's used to
# expose only limited set of fields and to do type transformation.
_PUBLIC_ATTRIBUTES = {
    'id': fields.String,
    'name': fields.String,
    'version': fields.String,
    'host_id': fields.String,
}


class Services(Resource):

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self, cluster_id):
        services = []

        try:
            hosts = db_api.get_hosts_by_cluster(cluster_id)
            for host in hosts:
                services += db_api.get_services_by_host(host['id'])

        except exceptions.NotFound as exc:
            abort(404, message=six.text_type(exc))

        services = sorted(services, key=lambda s: s['name'])
        return services
