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
import json
from celery import Celery
from gaia.parser import deserialize
from gaia.core import config

app = Celery('tasks',
             backend=config['gaia_celery']['celery_backend'],
             broker=config['gaia_celery']['celery_broker'])


@app.task
def parse_process(request_json):
    """
    Create a process of the specified name,
    parse a dict of process inputs and arguments,
    run the process, and return the output.
    :param process_name: Name of process to run, ie 'within'
    :param request_json: Dict of inputs and process args
    :return: GaiaIO object containing process output data
    """
    process = json.loads(request_json, object_hook=deserialize)
    process.compute()
    return process.output


@app.task
def execute_process(process, inputs=None, **kwargs):
    """
    Execute the input GaiaProcess object, first adding
    specified inputs and process args if any, and return
    the resulting output.
    :param process: A GaiaProcess object
    :param inputs: Optional GaiaIO objects specifying input data
    :param kwargs: Optional process arguments
    :return: GaiaIO object containing output data
    """
    if inputs:
        process.inputs = inputs
    if kwargs and process.args is None:
        process.args = {}
    for k, v in kwargs.items():
        process.args[k] = v
    process.compute()
    return process.output
