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


# This can be run from the command line in the gaia source folder as follows:
#
