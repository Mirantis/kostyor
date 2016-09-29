import uuid
import datetime

from kostyor.db import models
from kostyor.db import api as db_api

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from oslotest import base

from kostyor.common import constants, exceptions


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

        self.assertGreater(len(result), 0)

        result_data = result[0]

        self.assertIsNotNone(result_data['id'])

    def test_get_all_clusters(self):

        for i in range(0, 10):
            db_api.create_cluster("test" + str(i), constants.MITAKA,
                                  constants.READY_FOR_UPGRADE)

        expected = db_api.get_clusters()

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

    def test_get_upgrades(self):
        expected = [
            {
                'id': str(uuid.uuid4()),
                'cluster_id': str(uuid.uuid4()),
                'from_version': constants.MITAKA,
                'to_version': constants.NEWTON,
                'status': constants.UPGRADE_PAUSED,
                'upgrade_start_time': datetime.datetime.utcnow(),
                'upgrade_end_time': datetime.datetime.utcnow(),
            } for _ in range(0, 2)
        ]
        self.context.session.bulk_insert_mappings(models.UpgradeTask, expected)

        retrieved = db_api.get_upgrades()
        self.assertEqual(expected, retrieved)

    def test_get_upgrades_w_cluster_id(self):
        expected = [
            {
                'id': str(uuid.uuid4()),
                'cluster_id': str(uuid.uuid4()),
                'from_version': constants.MITAKA,
                'to_version': constants.NEWTON,
                'status': constants.UPGRADE_PAUSED,
                'upgrade_start_time': datetime.datetime.utcnow(),
                'upgrade_end_time': datetime.datetime.utcnow(),
            } for _ in range(0, 3)
        ]
        # make second entry to belong the same cluster as first one does
        expected[1]['cluster_id'] = expected[0]['cluster_id']
        self.context.session.bulk_insert_mappings(models.UpgradeTask, expected)

        retrieved = db_api.get_upgrades(expected[0]['cluster_id'])
        self.assertEqual(expected[0:2], retrieved)

    def test_create_cluster_upgrade(self):
        cluster = db_api.create_cluster("test",
                                        constants.MITAKA,
                                        constants.READY_FOR_UPGRADE)
        upgrade = db_api.create_cluster_upgrade(cluster['id'],
                                                constants.NEWTON)

        self.assertIsNotNone(upgrade['id'])
        self.assertEqual(cluster['id'], upgrade['cluster_id'])
        self.assertEqual(constants.MITAKA, upgrade['from_version'])
        self.assertEqual(constants.NEWTON, upgrade['to_version'])

    def test_create_cluster_upgrade_not_found(self):
        self.assertRaises(exceptions.ClusterNotFound,
                          db_api.create_cluster_upgrade,
                          'non-existing-id',
                          constants.NEWTON)

    def test_create_cluster_upgrade_version_unknown(self):
        cluster = db_api.create_cluster("test",
                                        constants.UNKNOWN,
                                        constants.READY_FOR_UPGRADE)
        self.assertRaises(exceptions.ClusterVersionIsUnknown,
                          db_api.create_cluster_upgrade,
                          cluster['id'],
                          constants.NEWTON)

    def test_create_cluster_upgrade_in_progress(self):
        cluster = db_api.create_cluster("test",
                                        constants.MITAKA,
                                        constants.UPGRADE_IN_PROGRESS)
        self.assertRaises(exceptions.UpgradeIsInProgress,
                          db_api.create_cluster_upgrade,
                          cluster['id'],
                          constants.NEWTON)

    def test_create_cluster_upgrade_lower_version(self):
        cluster = db_api.create_cluster("test",
                                        constants.MITAKA,
                                        constants.READY_FOR_UPGRADE)
        self.assertRaises(exceptions.CannotUpgradeToLowerVersion,
                          db_api.create_cluster_upgrade,
                          cluster['id'],
                          constants.LIBERTY)

    def test_cancel_cluster_upgrade_cluster_not_found(self):
        self.assertRaises(exceptions.ClusterNotFound,
                          db_api.cancel_cluster_upgrade,
                          'non-existing-id')

    def test_continue_cluster_upgrade_cluster_not_found(self):
        self.assertRaises(exceptions.ClusterNotFound,
                          db_api.continue_cluster_upgrade,
                          'non-existing-id')

    def test_pause_cluster_upgrade_cluster_not_found(self):
        self.assertRaises(exceptions.ClusterNotFound,
                          db_api.pause_cluster_upgrade,
                          'non-existing-id')

    def test_rollback_cluster_upgrade_cluster_not_found(self):
        self.assertRaises(exceptions.ClusterNotFound,
                          db_api.rollback_cluster_upgrade,
                          'non-existing-id')
