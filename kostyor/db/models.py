from kostyor.common import constants

import sqlalchemy as sa
from sqlalchemy import orm

from oslo_utils import uuidutils

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class HasId(object):
    """id mixin, add to subclasses that have an id."""
    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)


class Cluster(Base, HasId):
    __tablename__ = 'clusters'

    name = sa.Column(sa.String(255))
    version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))

    status = sa.Column(sa.Enum(*constants.STATUSES))

    def __init__(self, name, version, status):
        super(Cluster, self).__init__()
        self.name = name
        self.version = version
        self.status = status

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'version':
                self.version, 'status': self.status}


class Host(Base, HasId):
    __tablename__ = 'hosts'

    hostname = sa.Column(sa.String(255))
    cluster_id = sa.Column(sa.ForeignKey('clusters.id'))


class Service(Base, HasId):
    __tablename__ = 'services'

    name = sa.Column(sa.String(255))
    host_id = sa.Column(sa.ForeignKey('hosts.id'))
    version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))


class UpgradeTask(Base, HasId):
    __tablename__ = 'upgrade_tasks'
    cluster_id = sa.Column(sa.ForeignKey('clusters.id'))
    from_version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))
    to_version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))
    upgrade_start_time = sa.Column(sa.DateTime)
    upgrade_end_time = sa.Column(sa.DateTime)
    status = sa.Column(sa.Enum(*constants.STATUSES))

    def to_dict(self):
        return {'id': self.id,
                'cluster_id': self.cluster_id,
                'from_version': self.from_version,
                'to_version': self.to_version,
                'upgrade_start_time': self.upgrade_start,
                'upgrade_end_time': self.upgrade_end_time,
                'status': self.status
                }


class ServiceUpgradeRecord(Base, HasId):
    __tablename__ = 'service_upgrade_records'

    service_id = sa.Column(sa.ForeignKey('services.id'))
    upgrade_task_id = sa.Column(sa.ForeignKey('upgrade_tasks.id'))

    service = orm.relationship(Service,
                               backref=orm.backref('services',
                                                   cascade='delete'))
    upgrade = orm.relationship(UpgradeTask,
                               backref=orm.backref('upgrade_tasks',
                                                   cascade='delete'))

    status = sa.Column(sa.Enum(*constants.STATUSES))
