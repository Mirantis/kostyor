#!/usr/bin/python
import requests
import sys
import ConfigParser

from cliff.command import Command
from cliff.lister import Lister
from cliff.app import App
from cliff.commandmanager import CommandManager
from cliff.show import ShowOne

CONF = ConfigParser.ConfigParser()
CONF.read("conf.ini")
try:
    host = CONF.get('global', 'host')
except:
    host = "localhost"

try:
    port = CONF.get('global', 'port')
except:
    port = 80


def _make_request_with_cluser_id(http_method, endpoint, cluster_id):
    req_method = getattr(requests, http_method)
    return req_method('http://{}:{}/{}/{}'.format(host, port, endpoint,
                                                  cluster_id))


def _print_error_msg(resp):
    message = resp.json()['message']
    print('HTTP {}: {}'.format(resp.status_code, message))


class KostyorApp(App):
    def __init__(self):
        super(KostyorApp, self).__init__(
            description='Kostyor cli app',
            version='0.1',
            command_manager=CommandManager('kostyor.cli'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


class ClusterDiscovery(Command):
    description = ("Discover cluster using specified discovery "
                   "method <discovery_method> and setting it's "
                   "name to <cluster_name>")
    action = "discover-cluster"

    def discover(discovery_method, cluster_name, *args):
        # TODO validate discovery method
        # TODO run discovery using chosen method
        pass


class ClusterList(Lister):
    def take_action(self, parsed_args):
        columns = ('Cluster Name', 'Cluster ID', 'Status')

        data = requests.get('http://{}:{}/cluster-list'.format(host, port))
        clusters = data.json()['clusters']
        output = ((i['name'], i['id'], i['status']) for i in clusters)

        return (columns, output)


class ClusterStatus(ShowOne):
    description = ("Returns information about a cluster as a list of nodes "
                   "belonging to specified cluster and list of services "
                   "running on these nodes")
    action = "cluster-status"

    def get_parser(self, prog_name):
        parser = super(ClusterStatus, self).get_parser(prog_name)
        parser.add_argument('cluster_id')
        return parser

    def take_action(self, parsed_args):

        cluster_id = parsed_args.cluster_id
        columns = ('Cluster ID', 'Cluster Name', 'OpenStack Version',
                   'Status',)
        data = requests.get(
            'http://{}:{}/cluster-status/{}'.format(host, port, cluster_id))
        output = ()
        if data.status_code == 200:
            data = data.json()
            output = (data[i].capitalize() for i in ['id', 'name', 'version',
                                                     'status'])
        else:
            _print_error_msg(data)
        return (columns, output)

    def get_status(cluster_id):
        r = _make_request_with_cluser_id('get', 'cluster-status', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get cluster status: %s' % message)
        result = r.json()
        return result


class ClusterUpgrade(ShowOne):
    description = "Kicks off an upgrade of specified cluster"
    action = "upgrade-cluster"

    def get_parser(self, prog_name):
        parser = super(ClusterUpgrade, self).get_parser(prog_name)
        for arg_name in ['cluster_id', 'to_version']:
            parser.add_argument(arg_name)
        return parser

    def take_action(self, parsed_args):
        cluster_id = parsed_args.cluster_id
        to_version = parsed_args.to_version
        columns = ('Cluster ID', 'Upgrade Status',)
        request_str = 'http://{}:{}/upgrade-cluster/{}'.format(host,
                                                               port,
                                                               cluster_id)
        data = requests.post(request_str,
                             data={'version': to_version})
        output = ()
        if data.status_code == 201:
            data = data.json()
            output = (data['id'], data['status'],)
        else:
            _print_error_msg(data)

        return (columns, output)

    def upgrade(cluster_id, to_version):
        r = _make_request_with_cluser_id('post', 'upgrade-cluster', cluster_id)
        if r.status_code != 201:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class UpgradeStatus(Lister):
    description = "Returns the status of a running upgrade"
    action = "upgrade-status"

    def get_parser(self, prog_name):
        parser = super(UpgradeStatus, self).get_parser(prog_name)
        parser.add_argument('upgrade_id')
        return parser

    def take_action(self, parsed_args):
        upgrade_id = parsed_args.upgrade_id

        res = _make_request_with_cluser_id('get', self.action, upgrade_id)

        columns = ('Service', 'Version', 'Count')

        return (columns, res)

    def get_status(upgrade_id):
        r = _make_request_with_cluser_id('get', 'upgrade-status', upgrade_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get upgrade status: %s' % message)
        result = r.json()
        return result


class PauseUpgrade(Command):
    description = ("Pauses running upgrade, so that it can be continued, so "
                   "that it can be continued and aborted")
    action = "upgrade-pause"

    def pause(cluster_id):
        r = _make_request_with_cluser_id('put', 'upgrade-pause', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class RollbackUpgrade(Command):
    description = ("Rollbacks running or paused upgrade, attempting to move "
                   "all the components on all cluster nodes to it's initial "
                   " versions")
    action = "upgrade-rollback"

    def rollback(cluster_id):
        r = _make_request_with_cluser_id('put', 'upgrade-rollback', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class CancelUpgrade(Command):
    description = ("Cancels running or paused upgrade. All the currently "
                   "running upgrades procedures will be finished")
    action = "upgrade-cancel"

    def cancel(cluster_id):
        r = _make_request_with_cluser_id('put', 'upgrade-cancel', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class ContinueUpgrade(Command):
    description = "Continues paused upgrade"
    action = "upgrade-continue"

    def continue_upgrade(cluster_id):
        r = _make_request_with_cluser_id('put', 'upgrade-continue', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class DiscoveryMethod(Command):
    description = "Kicks off an upgrade of specified cluster"
    action = "create-discovery-method"

    def create(method):
        r = requests.post(
            'http://{host}:{port}/discover-cluster'.format(
                host=host, port=port
            ),
            params={'method': method}
        )
        if r.status_code != 201:
            message = r.json()['message']
            raise Exception(message)


class ListUpgradeVersions(Lister):
    description = ("Show the supported versions that Kostyor is able to "
                   "upgrade")
    action = "list-upgrade-versions"

    def take_action(self, parsed_args):
        columns = ('From Version', 'To Version',)
        data = requests.get(
            'http://{}:{}/list-upgrade-versions'.format(host, port)).json()
        data = [i.capitalize() for i in data]
        versions = ((data[i], data[i+1]) for i in xrange(len(data) - 1))
        return (columns, versions)

    def list(cluster_id):
        r = _make_request_with_cluser_id('get', 'list-upgrade-versions')
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get list of upgrade versions: %s'
                            % message)
        result = r.json()
        return result


class CheckUpgrade(Lister):
    description = ("Returns list of available versions cluster can be "
                   "upgraded to")
    action = "check-upgrade"

    def get_parser(self, prog_name):
        parser = super(CheckUpgrade, self).get_parser(prog_name)
        parser.add_argument('cluster_id')
        return parser

    def take_action(self, parsed_args):
        cluster_id = parsed_args.cluster_id
        columns = ('Available Upgrade Versions',)
        request_str = 'http://{}:{}/upgrade-versions/{}'.format(host,
                                                                port,
                                                                cluster_id)
        data = requests.get(request_str)
        output = ()
        if data.status_code == 200:
            output = ((i.capitalize(),) for i in data.json())
        else:
            _print_error_msg(data)
        return (columns, output)


class ListDiscoveryMethods(Lister):
    description = ("Returns a list of available methods to discover the "
                   "hosts and services that comprise an OpenStack cluster")
    action = "list-discovery-methods"

    def take_action(self, parsed_args):
        columns = ('Discovery Method', 'Description')

        data = (('OpenStack', 'OpenStack based discovery using Keystone API'),
                ('Ansible-Inventory', "Discover a cluster, via ansible"),
                ('Puppet', 'Discover a cluster, via puppet'),
                ('Fuel', 'Discover a cluster, via Fuel'))

        return (columns, data)

    def list():
        r = requests.get(
            'http://{host}:{port}/discovery-methods'.format(
                host=host, port=port
            )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get list of discovery methods: %s'
                            % message)
        result = r.json()
        return result


def main(argv=sys.argv[1:]):
    myapp = KostyorApp()
    return myapp.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
