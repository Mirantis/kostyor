###################
Command Line Client
###################

Interacts with the Kostyor REST API.


Configuration
=============

* KOSTYOR_API_URL

* Username/password/credentials



Commands
========


* discover-cluster <discovery_method> <cluster_name> <args>

  * Uses <discovery_method> to map out a running OpenStack
    installation, to determine the nodes, and running services. Saves
    this information as <cluster_name> for easy retrieval

  ::

      kostyor discover-cluster openstack-discovery-method home_lab
      os_auth_url=devstack-1.coreitpro.com

* cluster-status <cluster_id>

  * Returns information about a cluster, such as the version of
    OpenStack it is running, if it is undergoing an upgrade, etc..


  :: 

      kostyor cluster-status home_lab


  Shows information about <cluster_id>

* upgrade-cluster <cluster_id> <to_version>

  * Kicks off an upgrade

  * Returns an upgrade_uuid


  ::
      
      kostyor upgrade-cluster home_lab mitaka

* upgrade-status <upgrade_uuid>

  * Returns the status of a running upgrade - should return how many
    nodes have been upgraded, other in-depth data

  ::

      kostyor upgrade-status UPGRADE_UUID

* upgrade-pause <cluster_id>

  * Pauses running upgrade, so that it can be continued and aborted
    later


  ::

      kostyor upgrade-pause home_lab

* upgrade-rollback <cluster_id>

  * Rollbacks running or paused upgrade, moving all the components
    to their initial versions


  ::

      kostyor upgrade-rollback home_lab

* upgrade-cancel <cluster_id>

  * Cancels running or paused upgrade. All the currently running
    upgrades will be finished


  ::

      kostyor upgrade-cancel home_lab

* upgrade-continue <cluster_id>

  * Continues paused upgrade


  ::

      kostyor upgrade-continue home_lab


* list-upgrade-versions <cluster_id>

  * Returns list of available versions to upgrade for cluster with
    specified id

  ::

      kostyor list-upgrade-versions home_lab


* list-discovery-methods

  * Returns a list of available methods to discover the hosts and
    services that comprise an OpenStack cluster

  ::

      kostyor list-discovery-methods






kostyor list-upgrades


cluster-status

* region name
* openstack-versions
* state
      * active
      * maintenance
      * error


        kostyor check-upgrade <cluster_id>

        returns:

        state
          in progress
          ready
      
        

cluster-component-list <cluster_id>

returns 

* component name
* component version
* can be upgraded?

could have multiple nova-cpus - with liberty, mitaka 


