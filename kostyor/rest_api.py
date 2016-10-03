import copy
import sys

from collections import defaultdict

from flask import Flask, jsonify, redirect, request, url_for
from flask_restful import Api
from keystoneauth1 import exceptions
from keystoneauth1 import session
from keystoneauth1.identity import v2
import six

from kostyor.common import constants
from kostyor import conf
from kostyor.inventory import discover
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


@app.route('/upgrade-status/<cluster_id>')
def get_upgrade_status(cluster_id):
    upgrade = db_api.get_upgrade_by_cluster(cluster_id)
    if upgrade:
        full_url = url_for(
            '.upgrade', cluster_id=cluster_id, upgrade_id=upgrade['id'])
        return redirect(full_url)
    else:
        return generate_response(404, 'Upgrade for cluster %s not found' %
                                 cluster_id)


@app.route('/discovery-methods')
def get_discovery_methods():
    methods = db_api.get_discovery_methods()
    items = [{'method': method} for method in methods]
    disc_methods = {'items': items}

    resp = jsonify(disc_methods)
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


@app.route('/create-discovery-method', methods=['POST'])
def create_discovery_method():
    discovery_method = request.form.get('method')
    disc_method = db_api.create_discovery_method(discovery_method)
    if not disc_method:
        resp = generate_response(
            404,
            'Failed to create discovery method: %s' % discovery_method
        )
        return resp

    resp = jsonify(disc_method)
    resp.status_code = 201
    return resp


@app.route('/discover-cluster', methods=['POST'])
def discover_cluster():
    discovery_method = str(request.form.get('method')).lower()

    # At this point only OpenStack-based discovery is implemented.
    if discovery_method == constants.OPENSTACK:
        sess = session.Session(auth=v2.Password(
            username=request.form.get('username'),
            password=request.form.get('password'),
            tenant_name=request.form.get('tenant_name'),
            auth_url=request.form.get('auth_url')))
        cluster_discovery = discover.OpenStackServiceDiscovery(sess)
        try:
            services = cluster_discovery.discover()
        except exceptions.ClientException as e:
            resp = generate_response(
                e.http_status,
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
