from flask import Flask
from flask import jsonify
from flask import request

from db import api as db_api
from inventory import upgrades
app = Flask(__name__)

@app.route('/cluster-status/<cluster_id>')
def get_cluster_status(cluster_id):
    cluster = db_api.get_cluster_status(cluster_id)
    if not cluster:
        message = {
                'status': 404,
                'message': 'Cluster %s not Found: ' % cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    resp = jsonify(cluster)
    return resp

@app.route('/upgrade-status/<cluster_id>')
def get_upgrade_status(cluster_id):
    upgrade = db_api.get_upgrade_status(cluster_id)
    if not upgrade:
        message = {
                'status': 404,
                'message': 'Upgrade for cluster %s not found: ' % cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    resp = jsonify(upgrade)
    return resp

@app.route('/discovery-methods')
def get_discovery_methods():
    disc_methods = db_api.get_discovery_methods()

    resp = jsonify(disc_methods)
    return resp

@app.route('/upgrade-versions/<cluster_id>')
def get_upgrade_versions(cluster_id):
    versions = db_api.get_upgrade_versions(cluster_id)
    if not versions:
        message = {
                'status': 404,
                'message': 'Get upgrade version failed for cluster %s' % cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    resp = jsonify(versions)
    return resp

@app.route('/discover-cluster', methods = ['POST'])
def create_discovery_method():
    discovery_method = request.args.get('method')
    disc_method = db_api.create_discovery_method(discovery_method)
    if not disc_method:
        message = {
                'status': 404,#TODO probable should fix it later
                'message': 'Failed to create discovery method: %s' %
                    discovery_method,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    resp = jsonify(disc_method)
    resp.status_code = 201
    return resp

@app.route('/upgrade-cluster/<cluster_id>', methods = ['POST'])
def create_cluster_upgrade(cluster_id):
    to_version = request.args.get('version')
    upgrade = db_api.create_cluster_upgrade(cluster_id, to_version)
    if not upgrade:
        message = {
                'status': 404,#TODO probable should fix it later
                'message': 'Failed to create cluster upgrade for cluster: %s' %
                    cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    resp = jsonify(upgrade)
    resp.status_code = 201
    return resp

@app.route('/upgrade-cancel/<cluster_id>', methods = ['PUT'])
def cancel_cluster_upgrade(cluster_id):
    upgrade = db_api.cancel_cluster_upgrade(cluster_id)
    if not upgrade:
        message = {
                'status': 404,#TODO probably should fix it later
                'message': 'Failed to cancel cluster upgrade for cluster: %s' %
                    cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    status = upgrades.cancel_upgrade(cluster_id)
    if status:
        #TODO: cancel failed, probably should update cluster upgrade status
        message = {
                'status': 500,#TODO probably should fix it later
                'message':
                    'Failed to cancel cluster upgrade for cluster: %s'
                    'with message %s' % (cluster_id, status)
        }
        resp = jsonify(message)
        resp.status_code = 500
        return resp

    resp = jsonify(upgrade)
    return resp

@app.route('/upgrade-continue/<cluster_id>', methods = ['PUT'])
def continue_cluster_upgrade(cluster_id):
    upgrade = db_api.continue_cluster_upgrade(cluster_id)
    if not upgrade:
        message = {
                'status': 404,#TODO probably should fix it later
                'message': 'Failed to continue cluster upgrade '
                'for cluster: %s' % cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    status = upgrades.continue_upgrade(cluster_id)
    if status:
        #TODO: continue failed, probably should update cluster upgrade status
        message = {
                'status': 500,#TODO probably should fix it later
                'message':
                    'Failed to continue cluster upgrade for cluster: %s'
                    'with message %s' % (cluster_id, status)
        }
        resp = jsonify(message)
        resp.status_code = 500
        return resp

    resp = jsonify(upgrade)
    return resp

@app.route('/upgrade-pause/<cluster_id>', methods = ['PUT'])
def pause_cluster_upgrade(cluster_id):
    upgrade = db_api.pause_cluster_upgrade(cluster_id)
    if not upgrade:
        message = {
                'status': 404,#TODO probably should fix it later
                'message': 'Failed to pause cluster upgrade for cluster: %s' %
                    cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    status = upgrades.pause_upgrade(cluster_id)
    if status:
        #TODO: pause failed, probably should update cluster upgrade status
        message = {
                'status': 500,#TODO probably should fix it later
                'message':
                    'Failed to pause cluster upgrade for cluster: %s'
                    'with message %s' % (cluster_id, status)
        }
        resp = jsonify(message)
        resp.status_code = 500
        return resp

    resp = jsonify(upgrade)
    return resp

@app.route('/upgrade-rollback/<cluster_id>', methods = ['PUT'])
def rollback_cluster_upgrade(cluster_id):
    upgrade = db_api.rollback_cluster_upgrade(cluster_id)
    if not upgrade:
        message = {
                'status': 404,#TODO probably should fix it later
                'message': 'Failed to rollback cluster upgrade'
                    ' for cluster: %s' % cluster_id,
        }
        resp = jsonify(message)
        resp.status_code = 404
        return resp

    status = upgrades.rollback_upgrade(cluster_id)
    if status:
        #TODO: rollback failed, probably should update cluster upgrade status
        message = {
                'status': 500,#TODO probably should fix it later
                'message':
                    'Failed to rollback cluster upgrade for cluster: %s'
                    'with message %s' % (cluster_id, status)
        }
        resp = jsonify(message)
        resp.status_code = 500
        return resp

    resp = jsonify(upgrade)
    return resp


if __name__ == '__main__':
    app.run()
