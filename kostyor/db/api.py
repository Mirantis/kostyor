"""
    return {'items': [{'id': cluster_id,
                       'name': 'tmp',
                       'status': 'ready'},
                      {'id': '9871',
                       'name': 'tmp2',
                       'status': 'updating'}]}
"""
def get_cluster_status(cluster_id):
    #TODO fix it later
    return {'id': cluster_id,
            'name': "Sean's Lab",
            'version': "Mitaka",
            'status': "READY",}

def get_upgrade_status(cluster_id):
    return {'id': cluster_id, 'status': 'upgrading'}

def get_discovery_methods():
    return {'items': [
                {'method': 'method1'},
                {'method': 'method2'}
            ]
           }

def get_upgrade_versions(cluster_id):
    return {'items': [
                {'version': 'version1'},
                {'version': 'version2'}
            ]
           }

def create_discovery_method(method):
    return {'id': '1', 'method': method}

def create_cluster_upgrade(cluster_id, to_version):
    return {'id': cluster_id, 'status': 'upgrading'}

def cancel_cluster_upgrade(cluster_id):
    return {'id': cluster_id, 'status': 'canceling'}

def continue_cluster_upgrade(cluster_id):
    return {'id': cluster_id, 'status': 'upgrading'}

def pause_cluster_upgrade(cluster_id):
    return {'id': cluster_id, 'status': 'paused'}

def rollback_cluster_upgrade(cluster_id):
    return {'id': cluster_id, 'status': 'rolling back'}

def get_clusters():
    return {'clusters': [{'id': 'TEST',
                         'name': 'Fake Cluster',
                         'status': 'READY'}] }
