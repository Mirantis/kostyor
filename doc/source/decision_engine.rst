Decision Engine
===============

Decision Engine is undoubtedly Kostyor's heart. It's intended to consolidate
a number of known facts about the cluster and produce a sequence of tasks
to be executed in order to do rolling upgrade.

Under the hood Decision Engine implements logic behind an upgrade scenario,
leaving crating tasks up to chosen upgrade driver. I.e. it asks driver to
produce upgrade tasks for OpenStack services, builds an upgrade scenario
on top of them and sends to execution. This allows to encapsulate deployment
specific additional steps inside driver, so it prepares a Celery chain [#]_
which will be used as execution unit (Celery task) later.

.. [#] http://docs.celeryproject.org/en/latest/userguide/canvas.html#chains


Strategy
--------

Decision Engine implements a certain approach of OpenStack upgrade procedure.
Thus, it seems reasonable to make it pluggable so one can change the approach
by using some third-party engine.

Built-in Kostyor's engine implements a node-by-node approach upgrading
services one-by-one in the order specified in OpenStack docs. [#]_

.. [#] http://docs.openstack.org/ops-guide/ops-upgrades.html

The order of nodes is determined based on services it hosts. Generally, they
are sorted according to services upgrade order. I.e. first goes nodes with
Keystone API, then with Glance API, then - Nova API and so on. It's important
to note that once a node is picked for upgrade, the whole list of services
will be upgraded on it one-by-one in the order specified in OpenStack docs.


Example
-------

Consider we have the following deployment setup:

- Node A

  - nova-api
  - nova-conductor
  - nova-scheduler
  - nova-spicehtml5proxy
  - neutron-l3-agent
  - neutron-metadata-agent
  - neutron-dhcp-agent
  - neutron-metering-agent
  - neutron-server
  - neutron-ns-metadata-proxy
  - neutron-linuxbridge-agent
  - glance-registry
  - glance-api

- Node B

  - nova-compute
  - neutron-linuxbridge-agent

- Node C

  - keystone-wsgi-public
  - keystone-wsgi-admin


In that case, Decision Engine will prepare the following upgrade scenario:

- Node C: keystone-wsgi-admin
- Node C: keystone-wsgi-admin
- Node A: glance-api
- Node A: glance-registry
- Node A: nova-conductor
- Node A: nova-scheduler
- Node A: nova-spicehtml5proxy
- Node A: nova-api
- Node A: neutron-server
- Node A: neutron-linuxbridge-agent
- Node A: neutron-l3-agent
- Node A: neutron-dhcp-agent
- Node A: neutron-metering-agent
- Node A: neutron-metadata-agent
- Node A: neutron-ns-metadata-proxy
- Node B: nova-compute
- Node B: neutron-linuxbridge-agent



Job control
-----------

Cancellation:

http://docs.celeryproject.org/en/latest/userguide/workers.html#revoke-revoking-tasks

http://docs.celeryproject.org/en/latest/reference/celery.app.control.html#celery.app.control.Control.discard_all

http://stackoverflow.com/a/15642110/705245


Pause:

http://docs.celeryproject.org/en/latest/reference/celery.app.control.html#celery.app.control.Control.cancel_consumer


Resume:

http://docs.celeryproject.org/en/latest/reference/celery.app.control.html#celery.app.control.Control.add_consumer
