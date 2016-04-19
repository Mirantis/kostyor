############
Architecture
############



General steps for an upgrade:

* Enumerate/Discover all the services running in an openstack cluster
* For each control node, upgrade the control plane services (nova-api, neutron-api, etc)
* For each resource node, Upgrade the resource services (nova-compute, neutron-agent) 

Class Hierarchy 
---------------


Upgrade objects:

Handles the actual mechanics of an upgrade. For example, a Grenade
based upgrade strategy invokes the Grenade script. Ansible based
upgrade strategy makes ansible calls, puppet does puppet calls, etc..

* UpgradeStrategy object

  * GrenadeUpgradeStrategy
  * AnsibleUpgradeStrategy



Inventory Management:

Handles the list of services running in an OpenStack cluster. 

Each API service appears to have corresponding API methods to
enumerate the list of services, where they are located, and their
health.


* InventoryManager

  * NovaHypervisorInventory

    * Based off nova hypervisor-list REST API call

  * AnsibleInventory


::

    stack@devstack-1:~/devstack$ nova service-list
    +----+------------------+--------------------------+----------+---------+-------+----------------------------+-----------------+
    | Id | Binary           | Host                     | Zone     | Status  | State | Updated_at                 | Disabled Reason |
    +----+------------------+--------------------------+----------+---------+-------+----------------------------+-----------------+
    | 3  | nova-conductor   | devstack-1.coreitpro.com | internal | enabled | up    | 2016-04-15T16:42:21.000000 | -               |
    | 4  | nova-cert        | devstack-1.coreitpro.com | internal | enabled | up    | 2016-04-15T16:42:19.000000 | -               |
    | 5  | nova-scheduler   | devstack-1.coreitpro.com | internal | enabled | up    | 2016-04-15T16:42:22.000000 | -               |
    | 6  | nova-compute     | devstack-3.coreitpro.com | nova     | enabled | up    | 2016-04-15T16:42:21.000000 | -               |
    | 7  | nova-consoleauth | devstack-1.coreitpro.com | internal | enabled | up    | 2016-04-15T16:42:19.000000 | -               |
    | 8  | nova-compute     | devstack-1.coreitpro.com | nova     | enabled | up    | 2016-04-15T16:42:20.000000 | -               |
    | 9  | nova-compute     | devstack-2.coreitpro.com | nova     | enabled | up    | 2016-04-15T16:42:22.000000 | -               |
    +----+------------------+--------------------------+----------+---------+-------+----------------------------+-----------------+
    stack@devstack-1:~/devstack$ neutron service-list
    Unknown command [u'service-list']
    stack@devstack-1:~/devstack$ neutron agent-list
    +--------------------------------------+--------------------+--------------------------+-------------------+-------+----------------+---------------------------+
    | id                                   | agent_type         | host                     | availability_zone | alive | admin_state_up | binary                    |
    +--------------------------------------+--------------------+--------------------------+-------------------+-------+----------------+---------------------------+
    | 06dc155d-73b8-40b8-be6e-3a5cbeb7d2e4 | Open vSwitch agent | devstack-1.coreitpro.com |                   | :-)   | True           | neutron-openvswitch-agent |
    | 1109ed7a-e374-409b-b154-15d9a1a0cacc | Metadata agent     | devstack-1.coreitpro.com |                   | :-)   | True           | neutron-metadata-agent    |
    | 486045bc-3fea-41e5-9663-5c58173816df | Open vSwitch agent | devstack-3.coreitpro.com |                   | :-)   | True           | neutron-openvswitch-agent |
    | 77b4178d-f2df-40d5-afc2-558cf4e9b03e | Open vSwitch agent | devstack-2.coreitpro.com |                   | :-)   | True           | neutron-openvswitch-agent |
    | 95175090-8dda-49ef-9357-22e58b716595 | DHCP agent         | devstack-1.coreitpro.com | nova              | :-)   | True           | neutron-dhcp-agent        |
    | af99b67d-c509-4d2f-8dbb-525f9ee12680 | L3 agent           | devstack-1.coreitpro.com | nova              | :-)   | True           | neutron-l3-agent          |
    +--------------------------------------+--------------------+--------------------------+-------------------+-------+----------------+---------------------------+
    stack@devstack-1:~/devstack$ nova hypervisor-list
    +----+--------------------------+-------+---------+
    | ID | Hypervisor hostname      | State | Status  |
    +----+--------------------------+-------+---------+
    | 1  | devstack-3.coreitpro.com | up    | enabled |
    | 2  | devstack-1.coreitpro.com | up    | enabled |
    | 3  | devstack-2.coreitpro.com | up    | enabled |
    +----+--------------------------+-------+---------+
