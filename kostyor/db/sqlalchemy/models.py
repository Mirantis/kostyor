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
    name = sa.Column(sa.String(255))
    version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))

    status = sa.Column(sa.Enum(*constants.STATUSES))


class Host(Base, HasId):

    hostname = sa.Column(sa.String(255))
    cluster_id = sa.Column(sa.ForeignKey('cluster.id'))

    cluster = orm.relationship(Cluster, backref=orm.backref("cluster",
                                                            cascade="delete"))


class Service(Base, HasId):
    name = sa.Column(sa.String(255))
    host_id = sa.Column(sa.String(255), sa.ForeignKey('host.id'))

    version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))

    host = orm.relationship(Host,
                            backref=orm.backref("host", cascade="delete"))


class UpgradeTask(Base, HasId):
    cluster_id = sa.Column(sa.ForeignKey('cluster.id'))
    from_version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))
    to_version = sa.Column(sa.Enum(*constants.OPENSTACK_VERSIONS))
    upgrade_start_time = sa.Column(sa.DateTime)
    # TODO(sc68cal) Think of a better column name?
    upgrade_end_time = sa.Column(sa.DateTime)

    cluster = orm.relationship(Cluster, backref=orm.backref("cluster",
                                                            cascade="delete"))
