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
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()


class DbApiTestCase(base.BaseTestCase):
    def setUp(self):
        super(DbApiTestCase, self).setUp()
        self.context = KostyorTestContext()
        db_api.db_session = self.context.session
        db_api.engine = self.context.engine
        models.Base.metadata.create_all(self.context.engine)
        self.context.session.commit()

    def tearDown(self):
        super(DbApiTestCase, self).tearDown()
        self.context.session.close()
        self.context.transaction.rollback()
        self.context.connection.close()

    def test_create_cluster(self):
        db_api.create_cluster("test", constants.MITAKA,
                              constants.READY_FOR_UPGRADE)

        result = db_api.get_clusters()

        self.assertIn("clusters", result)
        self.assertGreater(len(result['clusters']), 0)

        result_data = result['clusters'][0]

        self.assertIsNotNone(result_data['id'])

    def test_get_all_clusters(self):

        for i in range(0, 10):
            db_api.create_cluster("test" + str(i), constants.MITAKA,
                                  constants.READY_FOR_UPGRADE)

        expected = db_api.get_clusters()

        self.assertEqual(len(expected['clusters']), 10)

    def test_update_cluster(self):
        cluster = db_api.create_cluster("test", constants.MITAKA,
                                        constants.READY_FOR_UPGRADE)

        update = {"name": "foo!"}

        db_api.update_cluster(cluster['id'], **update)

        result = db_api.get_cluster(cluster['id'])

        self.assertEqual(update['name'], result['name'])
