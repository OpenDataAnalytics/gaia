import json

from celery import Celery
from gaia.parser import custom_json_deserialize
from gaia.core import config

app = Celery('tasks',
             backend=config['gaia']['celery_backend'],
             broker=config['gaia']['celery_broker'])


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
    process = json.loads(request_json, object_hook=custom_json_deserialize)
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
