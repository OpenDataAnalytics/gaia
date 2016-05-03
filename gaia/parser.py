#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc. and Epidemico Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
import argparse
import importlib
import inspect
import json
import gaia.inputs
import gaia.geo
from gaia.core import GaiaException

valid_classes = []
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.geo, inspect.isclass) if x[0].endswith('Process')])
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.inputs, inspect.isclass) if x[0].endswith('IO')])

# TODO: Need a method to register classes from domain specific code
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.geo.geo_inputs, inspect.isclass) if x[0].endswith('IO')])


def deserialize(dct):
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
            raise ImportError(
                'Not allowed to create class {}'.format(cls_name))
        del dct['_type']
        args = dct.get('args') or []
        if args:
            del dct['args']
        return cls(*args, **dct)
    return dct

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run geospatial process.')
    parser.add_argument('jsonfile', default=None,
                        help='JSON file to parse')
    args = parser.parse_args()
    with open(args.jsonfile) as infile:
            process = json.load(infile, object_hook=deserialize)
    process.compute()
    if hasattr(process, 'output') and hasattr(process.output, 'uri'):
        print("Result saved to {}".format(process.output.uri))
    else:
        print('Process complete.')
