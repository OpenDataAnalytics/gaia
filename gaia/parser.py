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
import logging
import gaia.geo
from gaia.core import get_plugins
from gaia.gaia_process import GaiaProcess
from gaia.inputs import GaiaIO

logger = logging.getLogger(__name__)


def add_to_dict(x):
    if issubclass(x[1], GaiaProcess):
        if x[1].required_inputs:
            valid_processes.append({x[0]: {y: getattr(x[1], y) for y in (
                'required_inputs', 'required_args',
                'optional_args', 'default_output')}})
    elif issubclass(x[1], GaiaIO):
        valid_inputs.append({x[0]: {y: getattr(x[1], y) for y in (
            'type', 'default_output')}})

valid_processes = []
valid_inputs = []

for mod in (gaia.geo.geo_inputs, gaia.inputs, gaia.geo):
    for x in inspect.getmembers(mod, inspect.isclass):
        add_to_dict(x)
for plugin in get_plugins():
    for x in inspect.getmembers(plugin, inspect.isclass):
        if x[1] in plugin.PLUGIN_CLASS_EXPORTS:
            add_to_dict(x)
valid_classes = [x.keys()[0] for x in valid_inputs] +\
                [y.keys()[0] for y in valid_processes]


def deserialize(dct):
    """
    Convert a JSON representation of a Gaia IO or Process
    into a Python object of the appropriate class
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
