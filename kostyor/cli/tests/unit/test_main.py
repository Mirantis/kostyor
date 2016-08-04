import mock
from oslotest import base
import requests

from kostyor_cli import main


class CLIUtilsTestCase(base.BaseTestCase):
    @mock.patch('kostyor_cli.main.host', '1.1.1.1')
    @mock.patch('kostyor_cli.main.port', '22')
    def test__make_request_with_cluster_id(self):
        requests.GET = mock.Mock()
        main._make_request_with_cluster_id('GET', 'endpoint',
                                           'cluster-id')
        requests.GET.assert_called_once_with(
            'http://1.1.1.1:22/endpoint/cluster-id')

    def test__make_request_with_cluster_id_wrong_http_method(self):
        self.assertRaises(AttributeError, main._make_request_with_cluster_id,
                          'SEND', 'endpoint', 'cluster-id')

    @mock.patch('sys.stdout')
    def test__print_error_msg(self, stdout_mock):
        resp = mock.Mock()
        resp.status_code = 400
        resp.json = mock.Mock(return_value={'message': 'Bad request'})
        stdout_mock.write = mock.Mock()
        main._print_error_msg(resp)
        stdout_mock.write.assert_any_call('HTTP 400: Bad request')


class CLIBaseTestCase(base.BaseTestCase):
    def setUp(self):
        super(CLIBaseTestCase, self).setUp()
        host_patcher = mock.patch('kostyor_cli.main.host', '1.1.1.1')
        port_patcher = mock.patch('kostyor_cli.main.port', '22')
        for patcher in [host_patcher, port_patcher]:
            patcher.start()
            self.addCleanup(patcher.stop)
        main._print_error_msg = mock.Mock()
        self.resp = mock.Mock()
        self.resp.status_code = 404
        self.resp.json = mock.Mock()
        self.app = main.KostyorApp()


class ClusterDiscoveryTestCase(CLIBaseTestCase):
    def setUp(self):
        super(ClusterDiscoveryTestCase, self).setUp()
        self.expected_request_params = {
            'method': 'openstack',
            'cluster_name': 'new-cluster',
            'auth_url': 'http://1.2.3.4',
            'username': 'admin',
            'tenant_name': 'admin',
            'password': 'qwerty',
        }
        self.expected_request_str = 'http://1.1.1.1:22/discover-cluster'
        self.command = ['discover-cluster',
                        'openstack',
                        'new-cluster',
                        '--os-auth-url=http://1.2.3.4',
                        '--username=admin',
                        '--tenant-name=admin',
                        '--password=qwerty']
        requests.post = mock.Mock(return_value=self.resp)

    def test_discover_cluster(self):
        self.resp.status_code = 201
        self.app.run(self.command)
        requests.post.assert_called_once_with(
            self.expected_request_str,
            data=self.expected_request_params)
        self.assertEqual(False, main._print_error_msg.called)

    def test_discover_cluster_response_with_error(self):
        self.expected_request_params['method'] = 'fake-method'
        self.command[1] = 'fake-method'
        self.app.run(self.command)
        requests.post.assert_called_once_with(
            self.expected_request_str,
            data=self.expected_request_params)
        main._print_error_msg.assert_called_once_with(self.resp)


class ClusterListTestCase(CLIBaseTestCase):
    def test_cluster_list(self):
        requests.get = mock.Mock()
        expected_request_str = 'http://1.1.1.1:22/cluster-list'
        command = ['cluster-list', ]
        self.app.run(command)
        requests.get.assert_called_once_with(expected_request_str)


class ClusterStatusTestCase(CLIBaseTestCase):
    def setUp(self):
        super(ClusterStatusTestCase, self).setUp()
        self.expected_request_str = 'http://1.1.1.1:22/cluster-status/1234'
        self.command = ['cluster-status', '1234']
        requests.get = mock.Mock(return_value=self.resp)

    def test_cluster_status(self):
        self.resp.status_code = 200
        self.app.run(self.command)
        requests.get.assert_called_once_with(self.expected_request_str)
        self.assertEqual(False, main._print_error_msg.called)

    def test_cluster_status_response_with_error(self):
        self.app.run(self.command)
        requests.get.assert_called_once_with(self.expected_request_str)
        main._print_error_msg.assert_called_once_with(self.resp)


class ClusterUpgradeTestCase(CLIBaseTestCase):
    def setUp(self):
        super(ClusterUpgradeTestCase, self).setUp()
        self.expected_params = {'version': 'mitaka'}
        self.expected_request_str = 'http://1.1.1.1:22/upgrade-cluster/1234'
        self.command = ['upgrade-cluster',
                        '1234',
                        'mitaka']
        requests.post = mock.Mock(return_value=self.resp)

    def test_upgrade_cluster(self):
        self.resp.status_code = 201
        self.app.run(self.command)
        requests.post.assert_called_once_with(self.expected_request_str,
                                              data=self.expected_params)
        self.assertEqual(False, main._print_error_msg.called)

    def test_upgrade_cluster_response_with_error(self):
        self.app.run(self.command)
        requests.post.assert_called_once_with(self.expected_request_str,
                                              data=self.expected_params)
        main._print_error_msg.assert_called_once_with(self.resp)


class CheckUpgradeTestCase(CLIBaseTestCase):
    def setUp(self):
        super(CheckUpgradeTestCase, self).setUp()
        self.expected_request_str = 'http://1.1.1.1:22/upgrade-versions/1234'
        self.command = ['check-upgrade',
                        '1234']
        requests.get = mock.Mock(return_value=self.resp)

    def test_check_upgrade(self):
        self.resp.status_code = 200
        self.app.run(self.command)
        requests.get.assert_called_once_with(self.expected_request_str)
        self.assertEqual(False, main._print_error_msg.called)

    def test_check_upgrade_response_with_error(self):
        self.app.run(self.command)
        requests.get.assert_called_once_with(self.expected_request_str)
        main._print_error_msg.assert_called_once_with(self.resp)


class ListUpgradeVersionsTestCase(CLIBaseTestCase):
    def setUp(self):
        super(ListUpgradeVersionsTestCase, self).setUp()
        self.expected_request_str = 'http://1.1.1.1:22/list-upgrade-versions'
        self.command = ['list-upgrade-versions']

    def test_list_upgrade_versions(self):
        requests.get = mock.Mock(return_value=self.resp)
        self.app.run(self.command)
        requests.get.assert_called_once_with(self.expected_request_str)
        self.assertEqual(False, main._print_error_msg.called)
