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
             backend="ampq://guest@localhost//")


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
    first_df = vf_io1.read()
    second_df = vf_io2.read()

    first_within = first_df[first_df.geometry.within(
        second_df.geometry.unary_union)]

    return first_within


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
    # be called directly for synchronous execution
    out.data = task()

    out.write()




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
        process = parse_request(jsondata)

        print("Result saved to {}".format(process.output.uri))


# This can be run from the command line in the gaia source folder as follows:
#
