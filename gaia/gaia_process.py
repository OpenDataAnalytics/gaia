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
    required_inputs = {}
    required_args = {}
    optional_args = {}
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

    def validate(self):
        """
        Ensure that all required inputs and arguments are present.
        """
        # for input in self.inputs:
        #     if input.
        input_types = {}
        for input in self.inputs:
            type = input.type
            if type == types.PROCESS:
                for t in [i for i in dir(types) if not i.startswith("__")]:
                    if any((True for x in self.default_output if x in getattr(
                            formats, t, None))):
                        type = getattr(types, t)
                        break
            input_types[type] = input_types.setdefault(type, 0) + 1

        errors = []
        for input in self.required_inputs:
            min = self.required_inputs[input].get("min", 1)
            max = self.required_inputs[input].get("max", min)
            if input not in input_types.keys():
                errors.append(
                    "{} input(s) of type {} required for this process".format(
                        min, input))
            else:
                if input_types[input] < min:
                    errors.append("Not enough inputs of type {}".format(input))
                if max is not None and input_types[input] > max:
                    errors.append("Too many inputs of type {}".format(input))
        if errors:
            raise Exception(','.join(errors))
        for item in self.required_args.items():
            arg, arg_type = item[0], item[1]
            if not hasattr(self, arg) or getattr(self, arg) is None:
                raise GaiaException('Missing required argument {}'.format(arg))
            try:
                arg_type(getattr(self, arg))
            except:
                raise GaiaException('Required argument {} must be of type {}'
                                    .format(arg, arg_type))

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
