Fuel-CCP Driver
---------------

`Fuel CCP`_ is a project that deploys OpenStack via `Kubernetes`_.

A Kostyor driver that utilizes `Kubernetes rolling updates` to update
a Fuel-CCP cluster is planned.


Upgrading the "undercloud"
--------------------------

The `Kubernetes cluster management guide`_ discusses upgrading a
Kubernetes control plane.


Nodes can also be removed from a cluster using `kubectl drain`_

.. _Kubernetes: http://kubernetes.io
.. _Fuel CCP: http://fuel-ccp.readthedocs.io/en/latest/
.. _Kubernetes rolling updates: http://kubernetes.io/docs/user-guide/rolling-updates/
.. _Kubernetes cluster management guide: http://kubernetes.io/docs/admin/cluster-management/#upgrading-clusters-on-other-platforms
.. _kubectl drain: http://kubernetes.io/docs/admin/cluster-management/#maintenance-on-a-node
