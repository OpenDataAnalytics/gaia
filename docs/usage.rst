Usage
============

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