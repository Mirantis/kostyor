##########################
Kostyor roadmap for 2016Q3
##########################

Implement start OpenStack cluster upgrade procedure
===================================================

* Client
  * Implement upgrade-start, discover-cluster, cluster-list, list-upgrade-versions, cluster-status, check-upgrade cli commands

* REST API
  * Iplement REST API for all the commands listed in Client section

* Decision Engine
  * Implement determination of the sequence of steps to take for run/cancel the upgrade
  * Implement decision engine communication with task broker

* Task Broker
  * Implement managing of the task queue

* Job execution
  * Implement execution of steps of an upgrade

Integrate Kostyor with Downtimer tool
=====================================

* Job execution
  * Implement start of downtimer in case of running upgrade-start cli command and stop downtimer in case of crash of an upgrade procedure itself.
