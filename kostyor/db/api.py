import datetime
import six

from kostyor.common import constants, exceptions
from kostyor.db import models

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False))


def _get_most_recent_upgrade_task(cluster_id):
    q = db_session.query(models.UpgradeTask).filter_by(
        cluster_id=cluster_id).order_by(models.UpgradeTask.upgrade_start_time)
    return q.first()


def configure_session(database):
    engine = create_engine(database, convert_unicode=True)
    db_session.configure(bind=engine)


def shutdown_session(exception=None):
    # TODO dstepanenko: add handling for the case exception occured
    db_session.remove()


def get_cluster(cluster_id):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    if not cluster:
        raise Exception("Cluster with ID: %s not found" % cluster_id)
    return cluster.to_dict()


def get_upgrade_by_cluster(cluster_id):
    u_task = _get_most_recent_upgrade_task(cluster_id)
    return u_task.to_dict()


def get_upgrade(upgrade_id):
    u_task = db_session.query(models.UpgradeTask).get(upgrade_id)
    return u_task.to_dict()


def get_discovery_methods():
    return constants.DISCOVERY_METHODS


def get_upgrade_versions(cluster_id):
    return {'versions': constants.OPENSTACK_VERSIONS}


def create_discovery_method(method):
    return {'id': '1', 'method': method}


def create_cluster_upgrade(cluster_id, to_version):
    cluster = db_session.query(models.Cluster).get(cluster_id)

    if cluster is None:
        raise exceptions.ClusterNotFound(
            'Cluster "%s" not found.' % cluster_id)

    if cluster.version == constants.UNKNOWN:
        raise exceptions.ClusterVersionIsUnknown('Cluster version is unknown')

    if cluster.status == constants.UPGRADE_IN_PROGRESS:
        raise exceptions.UpgradeIsInProgress(
            'Cluster %s already has an upgrade in progress.' % cluster_id)

    if (constants.OPENSTACK_VERSIONS.index(cluster.version)
            >= constants.OPENSTACK_VERSIONS.index(to_version)):
        raise exceptions.CannotUpgradeToLowerVersion(
            'Upgrade procedure from "%s" to "%s" is not allowed.' % (
                cluster.version, to_version
            )
        )

    cluster.status = constants.UPGRADE_IN_PROGRESS
    u_task = models.UpgradeTask()
    u_task.cluster_id = cluster_id
    u_task.from_version = cluster.version
    u_task.to_version = to_version
    u_task.upgrade_start_time = datetime.datetime.now()
    db_session.add(u_task)
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to start upgrade
    return u_task.to_dict()


def cancel_cluster_upgrade(cluster_id):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.upgrade_end_time = datetime.datetime.now()
    u_task.status = cluster.status = constants.UPGRADE_CANCELLED
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to cancel
    return {'id': cluster_id, 'status': constants.UPGRADE_CANCELLED}


def continue_cluster_upgrade(cluster_id):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.status = cluster.status = constants.UPGRADE_IN_PROGRESS
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to continue
    return {'id': cluster_id, 'status': constants.UPGRADE_IN_PROGRESS}


def pause_cluster_upgrade(cluster_id):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.status = cluster.status = constants.UPGRADE_PAUSED
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to pause
    return {'id': cluster_id, 'status': constants.UPGRADE_PAUSED}


def rollback_cluster_upgrade(cluster_id):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.status = cluster.status = constants.UPGRADE_ROLLBACK
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to start rollback
    return {'id': cluster_id, 'status': constants.UPGRADE_ROLLBACK}


def get_clusters():
    # TODO(ikalnitsky): implement pagination in params
    return [cluster.to_dict() for cluster in db_session.query(models.Cluster)]


def get_upgrades(cluster_id=None):
    query = db_session.query(models.UpgradeTask)

    if cluster_id is not None:
        query = query.filter_by(cluster_id=cluster_id)

    return [upgrade.to_dict() for upgrade in query]


def create_host(name, cluster_id):
    new_host = models.Host()
    new_host.hostname = name
    new_host.cluster_id = cluster_id
    db_session.add(new_host)
    db_session.commit()
    return {'id': new_host.id,
            'hostname': new_host.hostname,
            'cluster_id': new_host.cluster_id}


def get_hosts_by_cluster(cluster_id):
    hosts = db_session.query(models.Host).filter_by(
        cluster_id=cluster_id)
    return [host.to_dict() for host in hosts]


def create_service(name, host_id, version):
    new_service = models.Service()
    new_service.name = name
    new_service.host_id = host_id
    new_service.version = version
    db_session.add(new_service)
    db_session.commit()
    return {'id': new_service.id,
            'name': new_service.name,
            'host_id': new_service.host_id,
            'version': new_service.version}


def get_services_by_host(host_id):
    services = db_session.query(models.Service).filter_by(
        host_id=host_id)
    return [service.to_dict() for service in services]


def create_cluster(name, version, status):
    kwargs = {"name": name, "version": version, "status": status}
    cluster = models.Cluster(**kwargs)
    db_session.add(cluster)
    db_session.commit()
    return {'id': cluster.id,
            'name': cluster.name,
            'version': cluster.version,
            'status': cluster.status}


def update_cluster(cluster_id, **kwargs):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    for arg, val in six.iteritems(kwargs):
        setattr(cluster, arg, val)
    db_session.commit()
