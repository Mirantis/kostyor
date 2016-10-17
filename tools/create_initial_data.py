#!user/bin/env python

from kostyor.common import constants
from kostyor import conf
from kostyor.db import api


conf.parse_args()
api.configure_session(conf.CONF.database.connection)

api.create_cluster("test", constants.MITAKA,
                   constants.READY_FOR_UPGRADE)
api.db_session.commit()
