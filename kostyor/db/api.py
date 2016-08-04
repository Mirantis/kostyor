from kostyor.db.sqlalchemy import models


def get_cluster_status(context, cluster_id):
    # TODO fix it later
    return {'id': cluster_id,
            'name': "Sean's Lab",
            'version': "mitaka",
            'status': "READY"}


def get_upgrade_status(context, cluster_id):
    u_task = context.session.query(models.UpgradeTask).get(cluster_id)
    return u_task.to_dict()


def get_discovery_methods(context):
    return {'items': [{'method': 'method1'}, {'method': 'method2'}]}


def get_upgrade_versions(context, cluster_id):
    return {'items': [{'version': 'version1'}, {'version': 'version2'}]}


def create_discovery_method(context, method):
    return {'id': '1', 'method': method}


def create_cluster_upgrade(context, cluster_id, to_version):
    return {'id': cluster_id, 'status': 'upgrading'}


def cancel_cluster_upgrade(context, cluster_id):
    return {'id': cluster_id, 'status': 'canceling'}


def continue_cluster_upgrade(context, cluster_id):
    return {'id': cluster_id, 'status': 'upgrading'}


def pause_cluster_upgrade(context, cluster_id):
    return {'id': cluster_id, 'status': 'paused'}


def rollback_cluster_upgrade(context, cluster_id):
    return {'id': cluster_id, 'status': 'rolling back'}


def get_clusters(context):
    return {'clusters': [{'id': 'TEST', 'name': 'Fake Cluster', 'status':
                          'READY'}]}


def create_host(context, name, cluster_id):
    return {'id': '1234',
            'name': name,
            'cluster_id': cluster_id}


def create_service(context, name, host_id, version):
    return {'id': '4321',
            'name': name,
            'host_id': host_id,
            'version': version}


def create_cluster(name, version, status):
    return {'id': '5678',
            'name': name,
            'version': version,
            'status': status}
