Usage
============

Python
-----------
Example usage in python::

    import gaia.inputs
    import gaia.geo
    import gaia.formats

    roads = gaia.inputs.PostgisIO('roads', columns=['ref', 'type', 'bridge'], filters=[('type','=','motorway'), ('bridge','=',1)])
    process = gaia.geo.LengthProcess(inputs=[iraq_roads])
    process.compute()
    process.output.read()[0:2]

                        ref      type  bridge  \
        0               A86  motorway       1
        1  A86/N11/D383;A86  motorway       1

                                                    geometry      length
        0  (LINESTRING (44.38284099999999 33.3747924, 44....  655.517362
        1  (LINESTRING (44.3859634 33.370603, 44.3845592 ...  651.974792

    process = gaia.geo.BufferProcess(inputs=[iraq_roads], buffer_size=1000)
    process.compute()
    process.output.uri

        '/data/output/c9b24b55-3fd7-430d-919b-d6cebe84c259/c9b24b55-3fd7-430d-919b-d6cebe84c259.json'

    process.output.read(format=gaia.formats.JSON)

        '{"type": "FeatureCollection", "features": [{"geometry": {"type": "MultiPolygon", "coordinates": [[[[44.30003419191555,.......


Additional usage examples can be found at http://gaia.readthedocs.org


Commandline
------------

Currently, Gaia can work from the commandline as follows::

    gaia ~/gaia/parser.py <JSON filename>


where <JSON filename> is a JSON file specifying the process, inputs, outputs, and arguments.

For example::

    gaia ~/gaia/parser.py within gaiatest.json

where gaiatest.json contains::

    {
      "_type": "gaia.geo.WithinProcess",
      "inputs": [
          {
              "_type": "gaia.inputs.VectorFileIO",
              "uri": "/data/iraq_hospitals.geojson"
          },
          {
              "_type": "gaia.inputs.ProcessIO",
              "process": {
              	  "_type": "gaia.geo.BufferProcess",
                  "name": "buffer",
                  "inputs": [
                      {
                          "_type": "gaia.inputs.VectorFileIO",
                          "uri": "/data/iraq_roads.geojson",
                          "filters": [
                              ["type", "=", "motorway"]
                          ]
                      }
                  ],
                  "buffer_size": 10000
              }
          }
      ]
    }

This will first run a subprocess (the second input) to generate a 1000 meter buffer around roads filtered by type 'motorway'.
The features of the first input will then be filtered to those within the generated buffer.