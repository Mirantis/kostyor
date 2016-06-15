############
Architecture
############

* Client

  * Used by an administrator to interact with the system
  * Run an upgrade
  * Check the status of a running upgrade
  * Pause a running upgrade
  * Rollback/abort/cancel a running upgrade

* Management panel / REST API

  * Responds to requests from the client
  * Issue alerts to tenants that an upgrade is in progress

* Discovery engine

  * Catalogs the pieces that make up an OpenStack cluster

* Decision Engine

  * Determines the sequence of steps to take for an upgrade
  * Forms tasks that are then given to task broker


* Task Broker

  * Manages the task queue

* Job execution

  * Executes the steps of an upgrade


Upgrade Workflow
================

* Enumerate/Discover all the services running in an OpenStack cluster
* For each control node, upgrade the control plane services (nova-api, neutron-api, etc)
* For each resource node:

  * Fence off the node so no new requests are scheduled on the node

    * i.e. Disable service record in Nova database for the node

  * Migrate resources off the node (tenant instances, tenant volumes)
  * Upgrade the resource services (nova-compute, neutron-agent)


Class Hierarchy
===============

Upgrade objects
---------------

Handles the actual mechanics of an upgrade. For example, a Grenade
based upgrade strategy invokes the Grenade script. Ansible based
upgrade strategy makes ansible calls, puppet does puppet calls, etc..

* UpgradeStrategy object

  * GrenadeUpgradeStrategy
  * AnsibleUpgradeStrategy



Inventory Management
--------------------

Handles the list of services running in an OpenStack cluster.

Each API service appears to have corresponding API methods to
enumerate the list of services, where they are located, and their
health.


* InventoryManager

  * OpenStack based InventoryManager

    * Uses OpenStack API calls and OpenStack admin API calls to
      collect list of hosts and services

      * nova hypervisor-list REST API call
      * keystone endpoint-list REST API call
      * neutron agent-list REST API call

  * AnsibleInventory

    * Uses Ansible inventory mechanism

  * PuppetInventory

    * Uses Puppet mechanism
  * CratonInventory

    * Uses `Craton <https://github.com/rackerlabs/craton/>`_ for inventory management

Types of Upgrades
=================

* Service upgrade

  * Upgrading of services on a node.

* Node/Host upgrade

  * Upgrading of the node operating system, or dependencies of
    services (kvm, libvirt, etc)

Node/Host Upgrade Strategies
----------------------------

* Nodes with persistent data have to be upgraded carefully

  * Either data is replicated so that it can be nuked and paved
  * Or in-place upgrade, and ensure no data is corrupted

* Nodes that don't - nuke and pave

  * Nova compute nodes *should be* stateless, so should be able to just
    nuke and pave


Service Upgrade Strategies
--------------------------


* Package Based

  * apt-get install --only-upgrade

* Source Based

  * git pull && python setup.py install

* Config-management based

  * Could use a tool like puppet, that installs either source or
    package


Handling Failures
-----------------

* If a node fails to upgrade:

  * Prompt admin for action? Fix manually, retry upgrade (transient failure), or abort upgrade?

  * Have a percentage of threshold where if exceeds - pause upgrade?
    5% of all computes?

  * Monitoring tenant instances - if outage occurs - pause the
    upgrade?
