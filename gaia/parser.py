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
import gaia.geo.processes_raster
import gaia.geo.processes_vector
import gaia.geo.processes_twitter
from gaia.core import GaiaException

_process_r = [(x[0].replace('Process', ''), x[1]) for x in inspect.getmembers(
    gaia.geo.processes_raster, inspect.isclass) if x[0].endswith('Process')]
_process_v = ([(x[0].replace('Process', ''), x[1]) for x in inspect.getmembers(
    gaia.geo.processes_vector, inspect.isclass) if x[0].endswith('Process')])
_process_t = ([(x[0].replace('Process', ''), x[1]) for x in inspect.getmembers(
    gaia.geo.processes_twitter, inspect.isclass) if x[0].endswith('Process')])
_processes = dict(_process_r + _process_v + _process_t)

valid_classes = []
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.geo, inspect.isclass) if x[0].endswith('Process')])
valid_classes.extend([x[0] for x in inspect.getmembers(
    gaia.inputs, inspect.isclass) if x[0].endswith('IO')])


def deserialize(dct):
    """
    Convert a JSON object into a class
    :param dct: The JSON object
    :return: An object of class which the JSON represents
    """
    process = None
    data = None

    def __init__(self, process_name, data=None, parse=True, parent=None):
        """
        Create an instance of GaiaRequestParser
        """
        self.process = create_process(process_name, parent=parent)
        if data and parse:
            self.parse(data)

    def parse(self, data=None):
        """
        Generate process and input objects from JSON data
        """
        if not data:
            data = self.data
        if isinstance(data, string_types):
            data = json.loads(data)
        process_inputs = data['data_inputs']
        self.process.args = data['args'] if 'args' in data else None
        self.process.inputs = []
        for input in process_inputs:
            io = create_io(self.process, input)
            self.process.inputs.append(io)
        return self.process


def is_vector(filename):
    """
    Return true if the filename appears to be a vector, False otherwise
    :param filename: name of file
    :return: boolean
    """
    try:
        return os.path.splitext(filename)[1] in gaia.formats.VECTOR
    except IndexError:
        return False


def create_io(process, data):
    """
    Create subclassed GaiaIO objects based on JSON configuration
    :param process: The process that will contain the GaiaIO objects
    :param data: The JSON configuration
    :return: Subclassed GaiaIO object
    """
    if data['source'] == 'file':
        io = gaia.inputs.VectorFileIO(**data) if is_vector(
            data['uri']) else gaia.inputs.RasterFileIO(**data)
    elif data['source'] == 'process':
        process_name = data['process']['name']
        parser = GaiaRequestParser(process_name,
                                   data=data['process'], parent=process.id)
        io = gaia.inputs.ProcessIO(process=parser.process)
    elif data['source'] == 'features':
        io = gaia.inputs.FeatureIO(**data)
    elif data['source'] == 'twitter':
        io = gaia.inputs.TwitterIO(**data)
    else:
        raise NotImplementedError()
    return io


def create_process(name, parent=None):
    """
    Return an object of a particular Process class based on the input string.
    :param name:
    :return:
    """
    try:
        return _processes[name[0].capitalize() + name[1:]](parent=parent)
    except AttributeError:
        raise GaiaException(traceback.format_exc())


def parse_request(process, request_json):
    """
    Parse a JSON request using GaiaRequestParser to return a GaiaProcess
    :param process: The process name ('within', 'subet', etc)
    :param request_json: The process configuration in JSON format
    :return: A GaiaProcess object
    """
    parser = GaiaRequestParser(process, request_json, parse=True)
    parser.process.compute()
    return parser.process

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
