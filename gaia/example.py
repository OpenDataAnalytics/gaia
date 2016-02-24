# This can be run from the command line in the gaia source folder as follows:
#
# $> python gaia/example.py example.json
#
#   and
#
# $> python gaia/example.py example2.json
#
#
# example.json just runs a buffer on iraq_roads.geojson.  The JSON can be equally
# equivallently expressed (in python) as:
#
#```python
# import gaia
# from gaia.inputs import VectorFileIO
# gaia.example.buffer(
#     VectorFileIO(uri="/opt/gaia/iraq_roads.geojson",
#                  filter={"type": "motorway"}), buffer_size=10000)
#```
#
# To run this asynchronously we would simply run the following:
#
#```python
# gaia.example.buffer.delay(
#     VectorFileIO(uri="/opt/gaia/iraq_roads.geojson",
#                  filter={"type": "motorway"}), buffer_size=10000)
#```
#
# The second example uses a celery 'chain'  the pythonic equvalent is:
#
#```python
# import gaia
# from celery.canvas import chain
# from gaia.inputs import VectorFileIO
#
# chain(gaia.example.buffer.s(
#           VectorFileIO(uri="/opt/gaia/iraq_roads.geojson",
#                    filter={"type": "motorway"}), buffer_size=10000),
#       gaia.example.within.s(
#           VectorFileIO(uri="/opt/gaia/iraq_hosptials.geojson",
#                    filter={"type": "motorway"}))()
#
#```
#
# In this example the output of the buffer operation becomes the first argument
# to the within function.  The chain function uses celery signatures. Signatures
# represent a celery task (i.e. a function) and its arguments,  but they do not
# have to represent the entire set of arguments.  For instance we could remove
# buffer_size  from the buffer example and pass it in later at execution time
# on the chain.  For example:
#
#```python
# c = chain(gaia.example.buffer.s(
#             VectorFileIO(uri="/opt/gaia/iraq_roads.geojson",
#                      filter={"type": "motorway"})),
#           gaia.example.within.s(
#             VectorFileIO(uri="/opt/gaia/iraq_hosptials.geojson",
#                      filter={"type": "motorway"}))
#
# c(buffer_size=10000) #=> Hospitals within 10,000 meters of a motorway
# c(buffer_size=1000)  #=> Hospitals within 1,000 meters of a motorway
# c(buffer_size=100)   #=> Hospitals within 1,00 meters of a motorway
#```
#
# Celery's canvas API - in addition to chains provides support for distributed
# groups, chords (map-reduce) map & starmap as well as chunks (scatter-gather).
# Please seee:  http://docs.celeryproject.org/en/latest/userguide/canvas.html for
# More information.

from __future__ import absolute_import
import argparse
from gaia.core import GaiaException
from geopandas import GeoDataFrame
from celery import Celery
from celery.canvas import signature
import importlib
import json

app = Celery('example',
             broker='amqp://guest@localhost//',
             backend="amqp://guest@localhost//")

# Note that the explicit 'name' part is only nesssiary
# because we are doing everything in one file and
# imports are getting screwed up.
@app.task(name="gaia.example.buffer")
def buffer(vf_io, buffer_size=None):
    first_df = vf_io.read()

    buffer = first_df.buffer(buffer_size)
    buffer_df = GeoDataFrame(geometry=buffer)

    return buffer_df

@app.task(name="gaia.example.within")
def within(vf_io1, vf_io2):
    # This should get moved into something that ensures
    # we're dealing with dataframes internally in the functions
    # functions shouldn't be responsible for dealing with reading
    # or loading data.
    try:
        first_df = vf_io1.read()
    except AttributeError:
        first_df = vf_io1

    try:
        second_df = vf_io2.read()
    except AttributeError:
        second_df = vf_io2


    second_within = second_df[second_df.geometry.within(
        first_df.geometry.unary_union)]

    return second_within


# This is a custom json deserializer that ensures
# that any dict with a "_type" key will show up as
# an object of the class defined in "_type", instantiated
# with the values in the dictionary.  It works recursively
# For the entire json being parsed. Moving forward we would
# Want to whitelist what classes are allowed,  to prevent
# security issues.

def custom_json_deserialize(dct):
    if "_type" in dct.keys():
        cls_name = dct['_type'].split(".")[-1]
        module_name = ".".join(dct['_type'].split(".")[:-1])

        cls = getattr(importlib.import_module(module_name), cls_name)
        del dct['_type']

        return cls(**dct)
    return dct

def parse_request(jsondata):
    out = jsondata['output']
    task = signature(jsondata, app=app)

    # At this point,  "task" is a celery task and can be called
    # with .delay() for async execution on a worker,  or it can
    # be called directly for synchronous execution - Here we just
    # call .apply() which will call the task in the local process.
    # This returns an "EagarResult" which has the same API as an
    # AsyncResult (e.g.,  to get the value we have to call '.result')
    out.data = task.apply().result
    out.write()

    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run geospatial process.')
    parser.add_argument('jsonfile')
    args = parser.parse_args()

    jsondata = None
    try:
        with open(args.jsonfile) as infile:
            jsondata = json.load(infile, object_hook=custom_json_deserialize)
    except Exception:
        print("You must supply a JSON file")

    if jsondata:
        output = parse_request(jsondata)
        print("Result saved to {}".format(output.uri))
