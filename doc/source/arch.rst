############
Architecture
############

* Client

  * Used by an administrator to interact with the system
  * Run an upgrade
  * Check the status of a running upgrade
  * Pause a running upgrade
  * Rollback/abort/cancel a running upgrade

* Management panel

  * Responds to requests from the client

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


Servie Upgrade Strategies
-------------------------


* Package Based

  * apt-get install --only-upgrade

* Source Based

  * git pull && python setup.py install

* Config-management based

  * Could use a tool like puppet, that installs either source or
    package


Types of Upgrades
-----------------

* Service upgrade

  * Upgrading of services on a node.

* Node/Host upgrade

  * Upgrading of the node operating system, or dependencies of
    services (kvm, libvirt, etc)
