from celery import Celery
from gaia.parser import parse_request
from gaia.core import config

app = Celery('tasks',
             backend=config['gaia_celery']['celery_backend'],
             broker=config['gaia_celery']['celery_broker'])


@app.task
def parse_process(process_name, request_json):
    """
    Create a process of the specified name,
    parse a dict of process inputs and arguments,
    run the process, and return the output.
    :param process_name: Name of process to run, ie 'within'
    :param request_json: Dict of inputs and process args
    :return: GaiaIO object containing process output data
    """
    process = parse_request(process_name, request_json)
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
