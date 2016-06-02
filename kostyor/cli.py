#!/usr/bin/python
import argparse
import os
import requests
import sys
import ConfigParser

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

#creating formated output for resulting tables
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

class ClusterDiscovery(object):
    description = ("Discover cluster using specified discovery "
                   "method <discovery_method> and setting it's "
                   "name to <cluster_name>")
    action = "discover-cluster"
    @staticmethod
    @args('--discovery_method', metavar='<discovery_method>',
          help="Discovery method that should be used for discovery of cluster")
    @args('--cluster_name', metavar='<cluster_name>', help='Cluster name')
    def discover(discovery_method, cluster_name, *args):
        #TODO validate discovery method
        #TODO run discovery using chosen method
        pass

class ClusterStatus(object):
    description = ("Returns information about a cluster as a list of nodes "
                   "belonging to specified cluster and list of services "
                   "running on these nodes")
    action = "cluster-status"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def get_status(cluster_id):
        r = requests.get('http://{host}:{port}/cluster-status/{cluster_id}'.format(
                            host=host, port=port, cluster_id=cluster_id
                         )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get cluster status: %s' % message)
        result = r.json()
        print_result(result)

class ClusterUpgrade(object):
    description = "Kicks off an upgrade of specified cluster"
    action = "upgrade-cluster"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    @args('--to_version', metavar='<to_version>')
    def upgrade(cluster_id, to_version):
        r = requests.post(
            'http://{host}:{port}/upgrade-cluster/{cluster_id}'.format(
                host=host, port=port, cluster_id=cluster_id
            ),
            params={'version': to_version}
        )
        if r.status_code != 201:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)

class UpgradeStatus(object):
    description = "Returns the status of a running upgrade"
    action = "upgrade-status"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def get_status(cluster_id):
        r = requests.get('http://{host}:{port}/upgrade-status/{cluster_id}'.format(
                            host=host, port=port, cluster_id=cluster_id
                         )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get upgrade status: %s' % message)
        result = r.json()
        print_result(result)

class PauseUpgrade(object):
    description = ("Pauses running upgrade, so that it can be continued, so "
                   "that it can be continued and aborted")
    action = "upgrade-pause"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def pause(cluster_id):
        r = requests.put(
            'http://{host}:{port}/upgrade-pause/{cluster_id}'.format(
                host=host, port=port, cluster_id=cluster_id
            )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)

class RollbackUpgrade(object):
    description = ("Rollbacks running or paused upgrade, attempting to move "
                   "all the components on all cluster nodes to it's initial "
                   " versions")
    action = "upgrade-rollback"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def rollback(cluster_id):
        r = requests.put(
            'http://{host}:{port}/upgrade-rollback/{cluster_id}'.format(
                host=host, port=port, cluster_id=cluster_id
            )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)

class CancelUpgrade(object):
    description = ("Cancels running or paused upgrade. All the currently "
                   "running upgrades procedures will be finished")
    action = "upgrade-cancel"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def cancel(cluster_id):
        r = requests.put(
            'http://{host}:{port}/upgrade-cancel/{cluster_id}'.format(
                host=host, port=port, cluster_id=cluster_id
            )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)

class ContinueUpgrade(object):
    description = "Continues paused upgrade"
    action = "upgrade-continue"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def continue_upgrade(cluster_id):
        r = requests.put(
            'http://{host}:{port}/upgrade-continue/{cluster_id}'.format(
                host=host, port=port, cluster_id=cluster_id
            )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception(message)
        ClusterStatus.get_status(cluster_id)

class DiscoveryMethod(object):
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

class ListUpgradeVersions(object):
    description = ("Returns list of available versions cluster can be "
                   "upgraded to")
    action = "list-upgrade-versions"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def list(cluster_id):
        r = requests.get(
            'http://{host}:{port}/upgrade-versions/{cluster_id}'.format(
                host=host, port=port, cluster_id=cluster_id
            )
        )
        if r.status_code != 200:
            message = r.json()['message']
            raise Exception('Failed to get list of upgrade versions: %s'
                            % message)
        result = r.json()
        print_result(result['items'])

class ListDiscoveryMethods(object):
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
    parser = argparse.ArgumentParser(
        description='Tool for dealing with openstack cluster upgrades'
    )
    add_command_parsers(parser)
    parsed_args = parser.parse_args(argv)
    action = parsed_args.action_fn
    del parsed_args.action_fn
    """ validating args for commands. The only parameter of the commands that
        can be set to None here is discovery_method, so all the remaining
        parameters should be set to some value """
    for arg, value in vars(parsed_args).items():
        if arg != 'discovery_method' and value is None:
            #TODO print help for exact command here
            parser.print_help()
            exit(os.EX_USAGE)

    action(**vars(parsed_args))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
