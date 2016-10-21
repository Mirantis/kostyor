#!user/bin/env python

from kostyor.common import constants
from kostyor import conf
from kostyor.db import api


conf.parse_args()
api.configure_session(conf.CONF.database.connection)

cluster = api.create_cluster("test", constants.MITAKA,
                             constants.READY_FOR_UPGRADE)

host = api.create_host("test-host", cluster["id"])
api.create_service("test-service", host['id'], constants.MITAKA)

api.db_session.commit()
