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
import os
import uuid
from gaia.core import get_abspath, config, GaiaException
from gaia import types, formats


class GaiaProcess(object):
    """
    Abstract class to define a geospatial process
    """

    # TODO: Enforce required inputs and args
    required_inputs = []
    required_args = []
    optional_args = [
        {
            'name': 'parent',
            'title': 'Parent ID',
            'description': 'Parent ID (UUID format)',
            'type': str
        }

    ]
    default_output = None
    args = None

    def __init__(self, inputs=None, output=None, parent=None, **kwargs):
        self.inputs = inputs
        self.output = output
        self.parent = parent
        self.id = str(uuid.uuid4())
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.validate()

    def test_arg_type(self, arg, arg_type):
        """
        Try to cast a process argument to its required type. Raise an
        exception if not successful.
        :param arg: The argument property
        :param arg_type: The required argument type (int, str, etc)
        """
        try:
            arg_type(getattr(self, arg))
        except Exception:
            raise GaiaException('Required argument {} must be of type {}'
                                .format(arg, arg_type))

    def validate(self):
        """
        Ensure that all required inputs and arguments are present.
        """
        # for input in self.inputs:
        #     if input.
        input_types = []
        errors = []

        for input in self.inputs:
            type = input.type
            if type == types.PROCESS:
                for t in [i for i in dir(types) if not i.startswith("__")]:
                    if any((True for x in input.default_output if x in getattr(
                            formats, t, []))):
                        type = getattr(types, t)
                        break
            input_types.append(type)

        for i, req_input in enumerate(self.required_inputs):
            if i >= len(input_types):
                errors.append("Not enough inputs for process")
            elif req_input['type'] != input_types[i]:
                errors.append("Input #{} is of incorrect type.".format(i+1))

        if len(input_types) > len(self.required_inputs):
            if (self.required_inputs[-1]['max'] is not None and
                len(input_types) > len(self.required_inputs) +
                    self.required_inputs[-1]['max']-1):
                errors.append("Incorrect # of inputs; expected {}".format(
                    len(self.required_inputs)))
            else:
                for i in range(len(self.required_inputs)-1, len(input_types)):
                    if input_types[i] != self.required_inputs[-1]['type']:
                        errors.append(
                            "Input #{} is of incorrect type.".format(i + 1))
        if errors:
            raise GaiaException('\n'.join(errors))
        for item in self.required_args:
            arg, arg_type = item['name'], item['type']
            if not hasattr(self, arg) or getattr(self, arg) is None:
                raise GaiaException('Missing required argument {}'.format(arg))
            self.test_arg_type(arg, arg_type)
            if 'options' in item and getattr(self, arg) not in item['options']:
                raise GaiaException('Invalid value for {}'.format(item['name']))
        for item in self.optional_args:
            arg, arg_type = item['name'], item['type']
            if hasattr(self, arg) and getattr(self, arg) is not None:
                self.test_arg_type(arg, arg_type)
                argval = getattr(self, arg)
                if 'options' in item and argval not in item['options']:
                    raise GaiaException(
                        'Invalid value for {}'.format(item['name']))

    def compute(self):
        """
        Abstract method for running process
        """
        raise NotImplementedError()

    def purge(self):
        """
        Delete the process output
        """
        self.output.delete()

    def get_outpath(self, uri=config['gaia']['output_path']):
        """
        Get the output path of the process

        :param uri: base output path
        :return: Process output path
        """
        ids_path = '{}/{}'.format(
            self.parent, self.id) if self.parent else self.id
        return get_abspath(
            os.path.join(uri, ids_path,
                         '{}{}'.format(self.id, self.default_output[0])))

    def get_input_classes(self):
        """
        Get the unique set of input classes

        :return: set of classes
        """
        io_classes = set()
        for input in self.inputs:
            input_class = input.__class__.__name__
            if 'Process' not in input_class:
                io_classes.add(input.__class__.__name__)
            else:
                io_classes = io_classes.union(input.process.get_input_classes())
        return io_classes
