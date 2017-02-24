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


def _get_cluster(cluster_id):
    cluster = db_session.query(models.Cluster).get(cluster_id)

    if cluster is None:
        raise exceptions.ClusterNotFound(
            'Cluster (ID="%s") not found.' % cluster_id
        )

    return cluster


def configure_session(database):
    engine = create_engine(database, convert_unicode=True)
    db_session.configure(bind=engine)


def shutdown_session(exception=None):
    # TODO dstepanenko: add handling for the case exception occured
    db_session.remove()


def get_cluster(cluster_id):
    return _get_cluster(cluster_id).to_dict()


def get_upgrade_by_cluster(cluster_id):
    u_task = _get_most_recent_upgrade_task(cluster_id)
    if u_task:
        return u_task.to_dict()
    else:
        raise exceptions.UpgradeNotFound("No upgrade found for Cluster ID %s"
                                         % cluster_id)


def get_upgrade(upgrade_id):
    u_task = db_session.query(models.UpgradeTask).get(upgrade_id)
    return u_task.to_dict()


def get_upgrade_versions(cluster_id):
    return {'versions': constants.OPENSTACK_VERSIONS}


def create_cluster_upgrade(cluster_id, to_version):
    cluster = _get_cluster(cluster_id)

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
    cluster = _get_cluster(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.upgrade_end_time = datetime.datetime.now()
    u_task.status = cluster.status = constants.UPGRADE_CANCELLED
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to cancel
    return {'id': cluster_id, 'status': constants.UPGRADE_CANCELLED}


def continue_cluster_upgrade(cluster_id):
    cluster = _get_cluster(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.status = cluster.status = constants.UPGRADE_IN_PROGRESS
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to continue
    return {'id': cluster_id, 'status': constants.UPGRADE_IN_PROGRESS}


def pause_cluster_upgrade(cluster_id):
    cluster = _get_cluster(cluster_id)
    u_task = _get_most_recent_upgrade_task(cluster_id)
    u_task.status = cluster.status = constants.UPGRADE_PAUSED
    db_session.commit()
    # TODO(sc68cal) RPC or calls to task broker to pause
    return {'id': cluster_id, 'status': constants.UPGRADE_PAUSED}


def rollback_cluster_upgrade(cluster_id):
    cluster = _get_cluster(cluster_id)
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
    return new_host.to_dict()


def get_hosts_by_cluster(cluster_id):
    # ensure cluster exists and throw ClusterNotFound if not
    cluster = _get_cluster(cluster_id)

    query = db_session.query(models.Host).filter_by(cluster_id=cluster.id)
    hosts = {host.id: host.to_dict() for host in query}

    query = db_session.query(models.hosts_services).filter(
        models.hosts_services.c.host_id.in_(hosts)
    )
    for record in query:
        host = hosts[record.host_id]
        host.setdefault('services', []).append(record.service_id)

    return list(hosts.values())


def get_host(host_id):
    return db_session.query(models.Host).get(host_id).to_dict()


def create_service(name, host_id, version):
    # TODO: get rid of `host_id` parameter as it's not always present
    host = db_session.query(models.Host).get(host_id)
    new_service = models.Service()
    new_service.name = name
    new_service.host_id = host_id
    new_service.version = version
    host.services.append(new_service)
    db_session.add(new_service)
    db_session.commit()
    return new_service.to_dict()


def get_services_by_host(host_id):
    query = db_session.query(models.Service).filter(
        models.Service.hosts.any(id=host_id)
    )
    services = {service.id: service.to_dict() for service in query}

    query = db_session.query(models.hosts_services).filter(
        models.hosts_services.c.service_id.in_(services)
    )
    for record in query:
        service = services[record.service_id]
        service.setdefault('hosts', []).append(record.host_id)

    return list(services.values())


def create_cluster(name, version, status):
    kwargs = {"name": name, "version": version, "status": status}
    cluster = models.Cluster(**kwargs)
    db_session.add(cluster)
    db_session.commit()
    return cluster.to_dict()


def update_cluster(cluster_id, **kwargs):
    cluster = db_session.query(models.Cluster).get(cluster_id)
    for arg, val in six.iteritems(kwargs):
        setattr(cluster, arg, val)
    db_session.commit()


def discover_cluster(name, info):
    """Create a cluster instance based on discovered information.

    :param name: a cluster name to be used
    :type name: str

    :param info: discovered information about the deployment
    :type info: dict
    """
    cluster = create_cluster(
        name,
        info.get('version', constants.UNKNOWN),
        info.get('status', constants.NOT_READY_FOR_UPGRADE)
    )

    objects = []
    cache = {}

    for hostname, services in info.get('hosts', {}).items():
        host = models.Host(hostname=hostname, cluster_id=cluster['id'])

        for service in services:
            if service['name'] not in cache:
                cache[service['name']] = models.Service(name=service['name'])
            host.services.append(cache[service['name']])
        objects.append(host)

    db_session.add_all(objects)
    db_session.commit()
    return cluster
