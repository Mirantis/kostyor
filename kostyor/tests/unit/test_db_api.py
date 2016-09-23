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
        self.cluster = db_api.create_cluster("test",
                                             constants.MITAKA,
                                             constants.READY_FOR_UPGRADE)
        self.context.session.commit()

    def tearDown(self):
        super(DbApiTestCase, self).tearDown()
        self.context.session.close()
        self.context.transaction.rollback()
        self.context.connection.close()

    def test_create_cluster(self):
        result = db_api.get_clusters()

        self.assertIn("clusters", result)
        self.assertGreater(len(result['clusters']), 0)

        result_data = result['clusters'][0]

        self.assertIsNotNone(result_data['id'])

    def test_get_all_clusters(self):

        for i in range(0, 10):
            db_api.create_cluster("test" + str(i), constants.MITAKA,
                                  constants.READY_FOR_UPGRADE)

        expected = db_api.get_clusters()['clusters']

        cluster_names = [cluster['name'] for cluster in expected]
        for i in range(0, 10):
            self.assertIn("test" + str(i), cluster_names)

    def test_update_cluster(self):
        update = {"name": "foo!"}

        db_api.update_cluster(self.cluster['id'], **update)

        result = db_api.get_cluster(self.cluster['id'])

        self.assertEqual(update['name'], result['name'])

    def test_discovery_methods(self):
        methods = db_api.get_discovery_methods()
        # we don't care about ordering here, so let's compare sorted arrays
        self.assertEqual(sorted(methods), sorted([constants.OPENSTACK]))

    def test_get_hosts_by_cluster_existing_cluster_success(self):
        host = db_api.create_host('hostname', self.cluster['id'])
        expected_result = [{'id': host['id'],
                            'hostname': 'hostname',
                            'cluster_id': self.cluster['id']}]

        result = db_api.get_hosts_by_cluster(self.cluster['id'])
        self.assertEqual(expected_result, result)

    def test_get_host_by_cluster_wrong_cluster_id_empty_list(self):
        result = db_api.get_hosts_by_cluster('fake-cluster-id')
        self.assertEqual([], result)

    def test_get_services_by_host_existing_cluster_success(self):
        host = db_api.create_host('hostname', self.cluster['id'])
        service = db_api.create_service('nova-api',
                                        host['id'],
                                        constants.MITAKA)
        expected_result = [{'id': service['id'],
                            'name': 'nova-api',
                            'host_id': host['id'],
                            'version': constants.MITAKA}]

        result = db_api.get_services_by_host(host['id'])
        self.assertEqual(expected_result, result)

    def test_get_services_by_host_wrong_host_id_empty_list(self):
        result = db_api.get_services_by_host('fake-host-id')
        self.assertEqual([], result)
