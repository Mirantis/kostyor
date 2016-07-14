import sqlalchemy as sa
from sqlalchemy import orm

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class HasId(object):
    """id mixin, add to subclasses that have an id."""
    id = sa.Column(sa.String(36),
                   primary_key=True,
                   default=uuidutils.generate_uuid)


class Cluster(Base, HasId):
    name = sa.Column(sa.String(255))
    version = sa.Column(sa.String(255))

    #TODO(sc68cal) change to Enum
    status = sa.Column(sa.String(255))


class Host(Base, HasId):

    hostname = sa.Column(sa.String(255))


class Service(Base, HasId):
    name = sa.Column(sa.String(255))
    host = sa.Column(sa.String(255), sa.ForeignKey('Host.id'))

    #TODO(sc68cal) Enum?
    version = sa.Column(sa.String(255))

class UpgradeTask(Base, HasId):
    pass
