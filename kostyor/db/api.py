from kostyor.db import models

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# TODO(sc68cal) save the database file in a configurable location
engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))


def get_cluster_status(db_session, cluster_id):
    # TODO fix it later
    return {'id': cluster_id,
            'name': "Sean's Lab",
            'version': "mitaka",
            'status': "READY"}


def get_upgrade_status(db_session, cluster_id):
    u_task = db_session.query(models.UpgradeTask).get(cluster_id)
    return u_task.to_dict()


def get_discovery_methods(db_session):
    return {'items': [{'method': 'method1'}, {'method': 'method2'}]}


def get_upgrade_versions(db_session, cluster_id):
    return {'items': [{'version': 'version1'}, {'version': 'version2'}]}


def create_discovery_method(db_session, method):
    return {'id': '1', 'method': method}


def create_cluster_upgrade(db_session, cluster_id, to_version):
    return {'id': cluster_id, 'status': 'upgrading'}


def cancel_cluster_upgrade(db_session, cluster_id):
    return {'id': cluster_id, 'status': 'canceling'}


def continue_cluster_upgrade(db_session, cluster_id):
    return {'id': cluster_id, 'status': 'upgrading'}


def pause_cluster_upgrade(db_session, cluster_id):
    return {'id': cluster_id, 'status': 'paused'}


def rollback_cluster_upgrade(db_session, cluster_id):
    return {'id': cluster_id, 'status': 'rolling back'}


def get_clusters(context):
    return {'clusters': [{'id': 'TEST', 'name': 'Fake Cluster', 'status':
                          'READY'}]}


def create_host(db_session, name, cluster_id):
    return {'id': '1234',
            'name': name,
            'cluster_id': cluster_id}


def create_service(db_session, name, host_id, version):
    return {'id': '4321',
            'name': name,
            'host_id': host_id,
            'version': version}


def create_cluster(db_session, name, version, status):
    kwargs = {"name": name, "version": version, "status": status}
    cluster = models.Cluster(**kwargs)
    db_session.add(cluster)
    return cluster
