================
Kostyor REST API
================


Status API
----------

GET /v1/cluster-status/<cluster-id>

GET /v1/upgrade-status/<cluster-id>

Discovery Method API
--------------------

GET /v1/discovery-methods

Returns list of supported discovery methods


Discovery API
-------------

POST /v1/discover-cluster/<disovery-method>

POST ARGS:
    * discovery method specific args
    
    Example: 
        
        POST /v1/discover-cluster/openstack-discovery-method/
        
        POST body contains args:  os_auth_url=devstack1.coreitpro.com
        

Upgrade API
-----------

POST /v1/upgrade-cluster/<cluster-id>

POST Body will contain the desired version

GET /v1/upgrade-versions/

List available versions for upgrade

Returns:
    * liberty
    * mitaka
    * etc..
    
POST /v1/upgrade-cancel/<cluster-id>

POST /v1/upgrade-continue/<cluster-id>

POST /v1/upgrade-pause/<cluster-id>

POST /v1/upgrade-rollback/<cluster-id>
