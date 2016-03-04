import argparse
import importlib
import inspect
import json
import gaia.formats
import gaia.inputs
import gaia.geo
from gaia.core import GaiaException

valid_classes = []
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.geo, inspect.isclass) if x[0].endswith('Process')])
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.inputs, inspect.isclass) if x[0].endswith('IO')])


def custom_json_deserialize(dct):
    """
    Convert a JSON object into a class
    :param dct: The JSON object
    :return: An object of class which the JSON represents
    """
    if "_type" in dct.keys():
        cls_name = dct['_type'].split(".")[-1]
        module_name = ".".join(dct['_type'].split(".")[:-1])
        cls = getattr(importlib.import_module(module_name), cls_name)
        if cls_name not in valid_classes:
            raise GaiaException(
                'Not allowed to create class {}'.format(cls_name))
        del dct['_type']
        args = dct.get('args') or []
        if args:
            del dct['args']
        return cls(*args, **dct)
    return dct

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run geospatial process.')
    parser.add_argument('--jsonstr', default=None,
                        help='String representation of JSON request')
    parser.add_argument('--jsonfile', default=None,
                        help='sum the integers (default: find the max)')
    args = parser.parse_args()

    jsondata = None
    if args.jsonstr:
        process = json.loads(args.jsonstr, object_hook=custom_json_deserialize)
    elif args.jsonfile:
        with open(args.jsonfile) as infile:
            process = json.load(infile, object_hook=custom_json_deserialize)
    else:
        print("You must supply either a JSON string or file")
    process.compute()
    print("Result saved to {}".format(process.output.uri))
