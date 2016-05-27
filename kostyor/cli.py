#!/usr/bin/python
import argparse
import sys

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
        pass

class ClusterStatus(object):
    description = ("Returns information about a cluster as a list of nodes "
                   "belonging to specified cluster and list of services "
                   "running on these nodes")
    @staticmethod
    action = "cluster-status"
    @args('--cluster_id', metavar='<cluster_id>')
    def get_status(cluster_id):
        pass

class ClusterUpgrade(object):
    description = "Kicks off an upgrade of specified cluster"
    action = "upgrade-cluster"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    @args('--to_version', metavar='<to_version>')
    def upgrade(cluster_id, to_version):
        pass

class UpgradeStatus(object):
    description = "Returns the status of a running upgrade"
    action = "upgrade-status"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def get_status(cluster_id):
        pass

class PauseUpgrade(object):
    description = ("Pauses running upgrade, so that it can be continued, so "
                   "that it can be continued and aborted")
    action = "upgrade-pause"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def pause(cluster_id):
        pass

class RollbackUpgrade(object):
    description = ("Rollbacks running or paused upgrade, attempting to move "
                   "all the components on all cluster nodes to it's initial "
                   " versions")
    action = "upgrade-rollback"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def rollback(cluster_id):
        pass

class CancelUpgrade(object):
    description = ("Cancels running or paused upgrade. All the currently "
                   "running upgrades procedures will be finished")
    action = "upgrade-cancel"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def cancel(cluster_id):
        pass

class ContinueUpgrade(object):
    description = "Continues paused upgrade"
    action = "upgrade-continue"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def continue_upgrade(cluster_id):
        pass

class ListUpgradeVersions(object):
    description = ("Returns list of available versions cluster can be "
                   "upgraded to")
    action = "list-upgrade-versions"
    @staticmethod
    @args('--cluster_id', metavar='<cluster_id>')
    def list(cluster_id):
        pass

class ListDiscoveryMethods(object):
    description = ("Returns a list of available methods to discover the "
                   "hosts and services that comprise an OpenStack cluster")
    action = "list-discovery-methods"
    @staticmethod
    def list():
        pass

CMD_OBJS = [ClusterDiscovery, ClusterStatus, ClusterUpgrade, UpgradeStatus,
            PauseUpgrade, RollbackUpgrade, CancelUpgrade, ContinueUpgrade,
            ListUpgradeVersions, ListDiscoveryMethods]

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
    action(**vars(parsed_args))

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
