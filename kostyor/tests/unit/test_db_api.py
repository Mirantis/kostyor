from kostyor.db import models
from kostyor.db import api as db_api

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from oslotest import base

from kostyor.common import constants


class KostyorTestContext(object):
    "Kostyor Database Context."
    engine = None
    session = None

    def __init__(self):
        self.engine = sa.create_engine('sqlite:///:memory:')
        self.session = sessionmaker(bind=self.engine)()


class DbApiTestCase(base.BaseTestCase):
    def setUp(self):
        super(DbApiTestCase, self).setUp()
        self.context = KostyorTestContext()
        models.Base.metadata.create_all(self.context.engine)

    def test_create_cluster(self):
        db_api.create_cluster(self.context.session, "test",
                              constants.MITAKA, constants.READY_FOR_UPGRADE)
        self.context.session.commit()

        result = db_api.get_clusters(self.context.session)

        self.assertIn("clusters", result)
        self.assertGreater(len(result['clusters']), 0)

        result_data = result['clusters'][0]

        self.assertIsNotNone(result_data['id'])
