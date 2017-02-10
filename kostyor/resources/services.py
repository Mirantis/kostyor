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
    'hosts': fields.List(fields.String, default=[]),
}


class Services(Resource):

    @marshal_with(_PUBLIC_ATTRIBUTES)
    def get(self, cluster_id):
        services = {}

        try:
            # Due to M-M relationship, the same instance may be returned
            # multiple times in this naive algorithm. Hence, we need to
            # ensure we are going to return it only once.
            hosts = db_api.get_hosts_by_cluster(cluster_id)
            for host in hosts:
                for service in db_api.get_services_by_host(host['id']):
                    if service['id'] not in services:
                        services[service['id']] = service

        except exceptions.NotFound as exc:
            abort(404, message=six.text_type(exc))

        services = sorted(services.values(), key=lambda s: s['name'])
        return services
