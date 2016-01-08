SimpleWPS
============

Gaia's SimpleWPS module makes it easier to send OGC Web Processing Service
(WPS) requests to remote servers.  These calls are made via Girder's web API
and accept parameters as simple JSON objects instead of verbose XML.

The following WPS processes are currently supported:

* vec:Query
* vec:Clip
* gs:collectGeometries
* gs:cropCoverage
* ras:RasterZonalStatistics

More processes will be added in the future.

WPS Server URL and Authentication
-----------------

A server url and basic auth string can be sent in the JSON of the request body::

    {
        "url": "http://demo.geonode.org/geoserver/wps",
        "auth": "Basic YWRtaW46Z2Vvc2VydmVy",
        ......
    }

A default url and basic auth string can also be set in the
gaia/server/gaia.local.cfg file (copied from gaia.dist.cfg)::

    [gaia]
    wps_default_url: "http://<your_server>/geoserver/wps"
    wps_default_auth: "Basic YWRtaW46Z2Vvc2VydmVy"


Making SimpleWPS calls
-----------------

The base URL for SimpleWPS calls is::

    http://<girder_url>/api/v1/simplewps/<wpsProcess>

where <wpsProcess> is the WPS process you wish to execute, minus the colon.
For example::

    http://localhost:8080/api/v1/simplewps/vecClip
    http://localhost:8080/api/v1/simplewps/rasRasterZonalStatistics
    http://localhost:8080/api/v1/simplewps/gsCollectGeometries

Sending blank JSON in the POST request body will bring back a JSON body
example for that process.  For instance, gsCollectGeometries::

    {
      "attribute": "<name of layer geometry attribute, default is the_geom>",
      "features": "<vector layer typename>",
      "filter": "<CQL query to filter clip layer by>"
    }

A WPS GetCapabilities request can be made via a GET request to the base URL,
along with optional request parameters for url, auth, and version.



