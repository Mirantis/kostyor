#!user/bin/env python

from kostyor.db import models
from kostyor.db.api import db_session


models.Base.metadata.create_all(db_session.bind)
