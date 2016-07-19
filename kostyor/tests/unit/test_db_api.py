from kostyor.db.sqlalchemy import models

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from oslotest import base


class KostyorTestContext(object):
    "Kostyor Database Context."
    engine = None
    session = None

    def __init__(self):
        self.engine = sa.create_engine('sqlite:///:memory:', echo=True)
        self.session = sessionmaker(bind=self.engine)()


class DbApiTestCase(base.BaseTestCase):
    def setUp(self):
        super(DbApiTestCase, self).setUp()
        self.context = KostyorTestContext()
        models.Base.metadata.create_all(self.context.engine)
