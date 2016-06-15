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
        return (('Cluster Name', 'Cluster ID', 'Status'),
                (("Jay's Lab",
                  "3e99896e-3199-11e6-ac61-9e71128cae77", "READY"),
                ("Sean's Lab",
                 "3e998d4c-3199-11e6-ac61-9e71128cae77", "READY")))


class ClusterStatus(ShowOne):
    description = ("Returns information about a cluster as a list of nodes "
                   "belonging to specified cluster and list of services "
                   "running on these nodes")
    action = "cluster-status"

    def get_parser(self, prog_name):
        parser = super(ClusterStatus, self).get_parser(prog_name)
        parser.add_argument('cluster-id')
        return parser

    def take_action(self, parsed_args):

        cluster_id = parsed_args.cluster_id

        columns = ('Cluster ID', 'Cluster Name', 'OpenStack Version', 'Status',)

        data = ("3e998d4c-3199-11e6-ac61-9e71128cae77", "Sean's Lab", "Mitaka",
                "READY",)

        return (columns, data)


    def get_status(cluster_id):
        r = _make_request_with_cluser_id('get', 'cluster-status', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get cluster status: %s' % message)
        result = r.json()
        return result


class ClusterUpgrade(Command):
    description = "Kicks off an upgrade of specified cluster"
    action = "upgrade-cluster"

    def upgrade(cluster_id, to_version):
        r = _make_request_with_cluser_id('post', 'upgrade-cluster', cluster_id)
        if r.status_code != 201:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class UpgradeStatus(Command):
    description = "Returns the status of a running upgrade"
    action = "upgrade-status"

    def get_status(cluster_id):
        r = _make_request_with_cluser_id('get', 'upgrade-status', cluster_id)
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
    description = ("Returns list of available versions cluster can be "
                   "upgraded to")
    action = "list-upgrade-versions"

    def take_action(self, parsed_args):
        return (('From Version', 'To Version',), (('Liberty', 'Mitaka'),
                                                  ('Mitaka', 'Newton'))
                )

    def list(cluster_id):
        r = _make_request_with_cluser_id('get', 'upgrade-versions', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get list of upgrade versions: %s'
                            % message)
        result = r.json()
        return result


class ListDiscoveryMethods(Lister):
    description = ("Returns a list of available methods to discover the "
                   "hosts and services that comprise an OpenStack cluster")
    action = "list-discovery-methods"

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
