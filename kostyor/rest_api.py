from collections import defaultdict

from flask import Flask
from flask import jsonify
from flask import request
from keystoneauth1 import exceptions
from keystoneauth1 import session
from keystoneauth1.identity import v2
import six

from kostyor.common import constants
from kostyor.db import api as db_api
from kostyor.db.sqlalchemy import models as db_models
from kostyor.inventory import discover
from kostyor.inventory import upgrades
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

app = Flask(__name__)

# TODO(sc68cal) save the database file in a configurable location
engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

def generate_response(status, message):
    message = {'status': status, 'message': message}
    resp = jsonify(message)
    resp.status_code = status
    return resp


@app.route('/cluster-status/<cluster_id>')
def get_cluster_status(cluster_id):
    cluster = db_api.get_cluster_status(cluster_id)
    if not cluster:
        resp = generate_response(404, 'Cluster %s not found' % cluster_id)
        return resp

    resp = jsonify(cluster)
    return resp


@app.route('/upgrade-status/<cluster_id>')
def get_upgrade_status(cluster_id):
    upgrade = db_api.get_upgrade_status(cluster_id)
    if not upgrade:
        resp = generate_response(
            404,
            'Upgrade for cluster %s not found' % cluster_id
        )
        return resp

    resp = jsonify(upgrade)
    return resp


@app.route('/discovery-methods')
def get_discovery_methods():
    methods = db_api.get_discovery_methods()
    items = [{'method': method} for method in methods]
    disc_methods = {'items': items}

    resp = jsonify(disc_methods)
    return resp


@app.route('/upgrade-versions/<cluster_id>')
def get_upgrade_versions(cluster_id):
    cluster = db_api.get_cluster_status(cluster_id)
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
    return jsonify(constants.OPENSTACK_VERSIONS)


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
                                            constants.UNDEFINED,
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
                                      constants.NOT_READY_FOR_UPGRADE)
    else:
        resp = generate_response(
            404,
            'Unsupported discovery method: %s' % discovery_method
        )
        return resp

    resp = jsonify(new_cluster)
    resp.status_code = 201
    return resp


@app.route('/upgrade-cluster/<cluster_id>', methods=['POST'])
def create_cluster_upgrade(cluster_id):
    to_version = request.form.get('version').lower()
    if (to_version not in constants.OPENSTACK_VERSIONS):
        resp = generate_response(
            400,
            'Unsupported version: %s' % to_version
        )
        return resp

    cluster = db_api.get_cluster_status(cluster_id)
    if (constants.OPENSTACK_VERSIONS.index(cluster['version']) >=
            constants.OPENSTACK_VERSIONS.index(to_version)):
        resp = generate_response(
            400,
            'Cluster version is the same or newer than %s' % to_version
        )
        return resp

    upgrade = db_api.create_cluster_upgrade(cluster_id, to_version)
    if not upgrade:
        resp = generate_response(
            404,  # TODO probable should fix it later
            'Failed to create cluster upgrade for cluster: %s' % cluster_id
        )
        return resp

    resp = jsonify(upgrade)
    resp.status_code = 201
    return resp


@app.route('/upgrade-cancel/<cluster_id>', methods=['PUT'])
def cancel_cluster_upgrade(cluster_id):
    upgrade = db_api.cancel_cluster_upgrade(cluster_id)
    if not upgrade:
        resp = generate_response(
            404,  # TODO probably should fix it later
            'Failed to cancel cluster upgrade for cluster: %s' % cluster_id
        )
        return resp

    status = upgrades.cancel_upgrade(cluster_id)
    if status:
        # TODO: cancel failed, probably should update cluster upgrade status
        resp = generate_response(
            500,  # TODO probably should fix it later
            'Failed to cancel cluster upgrade for cluster: %s'
            'with message %s' % (cluster_id, status)
        )
        return resp

    resp = jsonify(upgrade)
    return resp


@app.route('/upgrade-continue/<cluster_id>', methods=['PUT'])
def continue_cluster_upgrade(cluster_id):
    upgrade = db_api.continue_cluster_upgrade(cluster_id)
    if not upgrade:
        resp = generate_response(
            404,  # TODO probably should fix it later
            'Failed to continue cluster upgrade for cluster: %s' % cluster_id
        )
        return resp

    status = upgrades.continue_upgrade(cluster_id)
    if status:
        # TODO: continue failed, probably should update cluster upgrade status
        resp = generate_response(
            500,  # TODO probably should fix it later
            'Failed to continue cluster upgrade for cluster %s '
            'with message %s' % (cluster_id, status)
        )
        return resp

    resp = jsonify(upgrade)
    return resp


@app.route('/upgrade-pause/<cluster_id>', methods=['PUT'])
def pause_cluster_upgrade(cluster_id):
    upgrade = db_api.pause_cluster_upgrade(cluster_id)
    if not upgrade:
        resp = generate_response(
            404,  # TODO probably should fix it later
            'Failed to pause cluster upgrade for cluster: %s' % cluster_id
        )
        return resp

    status = upgrades.pause_upgrade(cluster_id)
    if status:
        # TODO: pause failed, probably should update cluster upgrade status
        resp = generate_response(
            500,  # TODO probably should fix it later
            'Failed to pause cluster upgrade for cluster %s with message %s'
            % (cluster_id, status)
        )
        return resp

    resp = jsonify(upgrade)
    return resp


@app.route('/upgrade-rollback/<cluster_id>', methods=['PUT'])
def rollback_cluster_upgrade(cluster_id):
    upgrade = db_api.rollback_cluster_upgrade(cluster_id)
    if not upgrade:
        resp = generate_response(
            404,  # TODO probably should fix it later
            'Failed to rollback cluster upgrade for cluster %s' % cluster_id
        )
        return resp

    status = upgrades.rollback_upgrade(cluster_id)
    if status:
        # TODO: rollback failed, probably should update cluster upgrade status
        resp = generate_response(
            500,  # TODO probably should fix it later
            'Failed to rollback cluster upgrade for cluster: %s '
            'with message %s' % (cluster_id, status)
        )
        return resp

    resp = jsonify(upgrade)
    return resp


@app.route('/cluster-list', methods=['GET'])
def cluster_list():
    clusters = db_api.get_clusters()
    if clusters:
        return jsonify(clusters)


if __name__ == '__main__':
    db_models.Base.metadata.create_all(bind=engine)
    app.run()
