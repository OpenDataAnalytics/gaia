Usage
============

Commandline
------------

Currently, Gaia works from the commandline as follows::

    gaia ~/gaia/parser.py <process_name> --jsonfile <filename>


where <process_name> is the process to run and <filename> is a JSON file specifying the process inputs, outputs, and arguments.

For example::

    gaia ~/gaia/parser.py within --jsonfile gaiatest.json

where gaiatest.json contains::


    {
      "data_inputs": {
          "first": {
              "type": "file",
              "uri": "/kitware/girder/plugins/gaia/tests/data/geoprocess/iraq_hospitals.geojson"
          },
          "second": {
              "type": "process",
              "process": {
                  "name": "buffer",
                  "data_inputs": {
                      "features": {
                          "type": "file",
                          "uri": "/kitware/girder/plugins/gaia/tests/data/geoprocess/iraq_roads.geojson",
                          "filter": {
                              "type": "motorway"
                          }
                      }
                  },
                  "args": {
                      "buffer_size": 10000
                  }
              }
          }
      }
    }

This will first run a subprocess (the second input) to generate a 1000 meter buffer around roads filtered by type 'motorway'.
The features of the first input will then be filtered to those within the generated buffer.

Girder
------------
Gaia is exposed through the Girder Web API at http://<your_girder_url>/api/v1#!/geoprocess, and accepts a processname ('buffer', 'within') and JSON body as input.


Girder Geoserver proxy
''''''''''''''''''''''

Gaia provides a proxy to the Geoserver instance of your choice.

  - Modify the 'ogc_url' setting in your gaia.local.cfg file to the URL of your Geoserver instance.

   - Make proxy requests to Geoserver from http://your-girder-url/geo/*::

       http://your-girder-url/geo/wms/?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities

       http://your-girder-url/geo/wfs/??request=GetFeature&version=1.1.0&typeName=topp:states&BBOX=-75.1,40.2,-72.3,41.6,EPSG:4326

       http://your-girder-url/geo/rest/workspaces/geonode/coveragestores/relief_san_andres.json

  - You can make GET, POST, and PUT requests.  You will need to add an Authorization header to your requests if authentication is required.

  - NOTE: If you have the minerva plugin enabled, the proxy will be available at ../girder/geo instead of ../geo
