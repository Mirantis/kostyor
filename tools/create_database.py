#!user/bin/env python

from kostyor.common import constants
from kostyor.db import models
from kostyor.db import api
from kostyor.db.api import db_session


models.Base.metadata.create_all(db_session.bind)

api.create_cluster(db_session, "test", constants.MITAKA,
                   constants.READY_FOR_UPGRADE)
db_session.commit()
