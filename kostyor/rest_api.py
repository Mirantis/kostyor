import copy
import sys

from flask import Flask, jsonify
from flask_restful import Api

from kostyor.common import constants
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
api.add_resource(resources.Discover, '/clusters/discover')
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


if __name__ == '__main__':
    conf.parse_args(sys.argv[1:])
    db_api.configure_session(conf.CONF.database.connection)
    app.run()
