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


  Show information about <cluster_id>

* upgrade <cluster_id> <to_version>

  * Kicks off an upgrade


  ::
      
      kostyor upgrade-cluster home_lab mitaka

* upgrade-status

  * Return the status of a running upgrade - should return how many
    nodes have been upgraded, other in-depth data

  ::

      kostyor upgrade-status home_lab
