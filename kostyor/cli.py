#!/usr/bin/python
import argparse
import os
import requests
import sys
import ConfigParser

from cliff.command import Command
from cliff.lister import Lister
from cliff.app import App
from cliff.commandmanager import CommandManager

CONF = ConfigParser.ConfigParser()
CONF.read("conf.ini")
host = CONF.get('global', 'host')
port = CONF.get('global', 'port')


# Decorators for actions
def args(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('args', []).insert(0, (args, kwargs))
        return func
    return _decorator


def methods_of(obj):
    """Get all callable methods of an object that don't start with underscore
    returns a list of tuples of the form (method_name, method, description)
    """
    result = []
    for i in dir(obj):
        if callable(getattr(obj, i)) and not i.startswith('_'):
            result.append(
                (
                    obj.action,
                    getattr(obj, i),
                    obj.description
                )
            )
    return result


def _make_request_with_cluser_id(http_method, endpoint, cluster_id):
    req_method = getattr(requests, http_method)
    return req_method('http://{}:{}/{}/{}'.format(host, port, endpoint,
                                                  cluster_id))

# creating formated output for resulting tables
# TODO(sc68cal) replace this with prettytable
# https://code.google.com/archive/p/prettytable/
def print_result(items):
    if not isinstance(items, list):
        items = [items]
    width = {}
    for item in items:
        for k, v in item.items():
            if k not in width:
                width[k] = len(v)
            else:
                if len(v) > width[k]:
                    width[k] = len(v)
    for k in items[0]:
        if len(k) > width[k]:
            width[k] = len(k)
    total_width = len(width) * 3 + 1 + sum(width.itervalues())

    print '-' * total_width
    for k in items[0]:
        print '| {:^{width}}'.format(k, width=width[k]),
    print '|'
    print '-' * total_width
    for item in items:
        for k, v in item.items():
            print '| {:^{width}}'.format(v, width=width[k]),
        print '|'
    print '-' * total_width


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

    @staticmethod
    @args('--discovery_method', metavar='<discovery_method>',
          help="Discovery method that should be used for discovery of cluster")
    @args('--cluster_name', metavar='<cluster_name>', help='Cluster name')
    def discover(discovery_method, cluster_name, *args):
        # TODO validate discovery method
        # TODO run discovery using chosen method
        pass


class ClusterStatus(Command):
    description = ("Returns information about a cluster as a list of nodes "
                   "belonging to specified cluster and list of services "
                   "running on these nodes")
    action = "cluster-status"

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def get_status(cluster_id):
        r = _make_request_with_cluser_id('get', 'cluster-status', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get cluster status: %s' % message)
        result = r.json()
        print_result(result)


class ClusterUpgrade(Command):
    description = "Kicks off an upgrade of specified cluster"
    action = "upgrade-cluster"

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    @args('--to_version', metavar='<to_version>')
    def upgrade(cluster_id, to_version):
        r = _make_request_with_cluser_id('post', 'upgrade-cluster', cluster_id)
        if r.status_code != 201:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class UpgradeStatus(Command):
    description = "Returns the status of a running upgrade"
    action = "upgrade-status"

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def get_status(cluster_id):
        r = _make_request_with_cluser_id('get', 'upgrade-status', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get upgrade status: %s' % message)
        result = r.json()
        print_result(result)


class PauseUpgrade(Command):
    description = ("Pauses running upgrade, so that it can be continued, so "
                   "that it can be continued and aborted")
    action = "upgrade-pause"

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
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

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
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

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def cancel(cluster_id):
        r = _make_request_with_cluser_id('put', 'upgrade-cancel', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class ContinueUpgrade(Command):
    description = "Continues paused upgrade"
    action = "upgrade-continue"

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def continue_upgrade(cluster_id):
        r = _make_request_with_cluser_id('put', 'upgrade-continue', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)


class DiscoveryMethod(Command):
    description = "Kicks off an upgrade of specified cluster"
    action = "create-discovery-method"

    @staticmethod
    @args('--method', metavar='<method>')
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

    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def list(cluster_id):
        r = _make_request_with_cluser_id('get', 'upgrade-versions', cluster_id)
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get list of upgrade versions: %s'
                            % message)
        result = r.json()
        print_result(result['items'])


class ListDiscoveryMethods(Lister):
    description = ("Returns a list of available methods to discover the "
                   "hosts and services that comprise an OpenStack cluster")
    action = "list-discovery-methods"

    @staticmethod
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
        print_result(result['items'])

CMD_OBJS = [ClusterDiscovery, ClusterStatus, ClusterUpgrade, UpgradeStatus,
            PauseUpgrade, RollbackUpgrade, CancelUpgrade, ContinueUpgrade,
            DiscoveryMethod, ListUpgradeVersions, ListDiscoveryMethods]


def add_command_parsers(parser):
    subparsers = parser.add_subparsers(help='sub-command help')
    for cmd in CMD_OBJS:
        command_object = cmd()
        for action, action_fn, desc in methods_of(command_object):
            cmd_parser = subparsers.add_parser(action, description=desc)
            for args, kwargs in getattr(action_fn, 'args', []):
                cmd_parser.add_argument(*args, **kwargs)
            cmd_parser.set_defaults(action_fn=action_fn)


def main(argv=sys.argv[1:]):
    myapp = KostyorApp()
    return myapp.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
