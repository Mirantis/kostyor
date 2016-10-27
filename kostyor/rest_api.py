import copy
import sys

from collections import defaultdict

from flask import Flask, jsonify, redirect, request, url_for
from flask_restful import Api
import six
from stevedore import driver
from stevedore import extension

from kostyor.common import constants
from kostyor.common import exceptions as k_exceptions
from kostyor import conf
from kostyor import resources

from kostyor.db import api as db_api

app = Flask(__name__)
api = Api(app)


# Flask-RESTful extends each 404 respond with custom message about close
# endpoints. It works pretty awful and unexpected when you explicitly
# specifies error message. Let's turn off it so any error message become
# predicted.
app.config['ERROR_404_HELP'] = False

# New API endpoints should be implemented via Flask-RESTful and added here.
# Once old ones are reimplemented - we can get rid of them and even provide
# some factory function to return Flask application.
api.add_resource(resources.Clusters, '/clusters')
api.add_resource(resources.Cluster, '/clusters/<cluster_id>')
api.add_resource(resources.Hosts, '/clusters/<cluster_id>/hosts')
api.add_resource(resources.Services, '/clusters/<cluster_id>/services')

api.add_resource(resources.Upgrades, '/upgrades')
api.add_resource(resources.Upgrade, '/upgrades/<upgrade_id>')


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_api.shutdown_session(exception)


def generate_response(status, message):
    message = {'status': status, 'message': message}
    resp = jsonify(message)
    resp.status_code = status
    return resp


def discovery_drivers():
    ext_manager = extension.ExtensionManager(
        namespace='kostyor.discovery_drivers')
    return ext_manager.names()


@app.route('/upgrade-status/<cluster_id>')
def get_upgrade_status(cluster_id):
    try:
        upgrade = db_api.get_upgrade_by_cluster(cluster_id)
        full_url = url_for(
            '.upgrade', cluster_id=cluster_id, upgrade_id=upgrade['id'])
        return redirect(full_url)
    except k_exceptions.UpgradeNotFound:
        return generate_response(404, 'Upgrade for cluster %s not found' %
                                 cluster_id)


@app.route('/discovery-methods')
def get_discovery_methods():
    resp = jsonify(discovery_drivers())
    return resp


@app.route('/upgrade-versions/<cluster_id>')
def get_upgrade_versions(cluster_id):
    cluster = db_api.get_cluster(cluster_id)
    if not cluster:
        resp = generate_response(404, 'Cluster %s not found' % cluster_id)
        return resp
    cluster_version_index = constants.OPENSTACK_VERSIONS.index(
        cluster['version'])
    upgrade_versions = (
        constants.OPENSTACK_VERSIONS[cluster_version_index + 1:])
    return jsonify(upgrade_versions)


@app.route('/list-upgrade-versions')
def list_upgrade_versions():
    res = copy.copy(constants.OPENSTACK_VERSIONS)
    res.remove(constants.UNKNOWN)
    return jsonify(res)


@app.route('/discover-cluster', methods=['POST'])
def discover_cluster():
    discovery_method = str(request.form.get('method')).lower()
    if discovery_method in discovery_drivers():
        discovery_args = {}
        for key in request.form:
            if key not in ['method', 'cluster_name']:
                discovery_args[key] = request.form.get(key, None)

        discovery_driver = driver.DriverManager(
            namespace='kostyor.discovery_drivers',
            name=discovery_method,
            invoke_on_load=True,
            invoke_kwds=discovery_args,
        ).driver
        try:
            services = discovery_driver.discover()
        except Exception as e:
            resp = generate_response(
                getattr(e, 'http_status', 404),
                e.message
            )
            return resp

        new_cluster = db_api.create_cluster(request.form.get('cluster_name'),
                                            constants.UNKNOWN,
                                            constants.NOT_READY_FOR_UPGRADE)
        host_service_map = defaultdict(list)
        for s in services:
            host_service_map[s[0]].append(s[1])
        hosts_ids = {}
        for host in host_service_map:
            hosts_ids[host] = db_api.create_host(host, new_cluster['id'])['id']
        for host, service in six.iteritems(host_service_map):
            for s in service:
                db_api.create_service(s, hosts_ids[host],
                                      constants.UNKNOWN)
    else:
        resp = generate_response(
            404,
            'Unsupported discovery method: %s' % discovery_method
        )
        return resp

    resp = jsonify(new_cluster)
    resp.status_code = 201
    return resp


if __name__ == '__main__':
    conf.parse_args(sys.argv[1:])
    db_api.configure_session(conf.CONF.database.connection)
    app.run()
