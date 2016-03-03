import argparse
import inspect
import json
import os
import traceback
from six import string_types
import gaia.formats
import gaia.inputs
import gaia.geo.processes_raster
import gaia.geo.processes_vector
from gaia.core import GaiaException

_process_r = [(x[0].replace('Process', ''), x[1]) for x in inspect.getmembers(
    gaia.geo.processes_raster, inspect.isclass) if x[0].endswith('Process')]
_process_v = ([(x[0].replace('Process', ''), x[1]) for x in inspect.getmembers(
    gaia.geo.processes_vector, inspect.isclass) if x[0].endswith('Process')])
_processes = dict(_process_r + _process_v)


class GaiaRequestParser(object):
    """
    Generate processes and inputs from a JSON object
    :return a GaiaProcess object
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
        self.process.args = data['args'] if 'args' in data else {}
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run geospatial process.')
    parser.add_argument('process')
    parser.add_argument('--jsonstr', default=None,
                        help='String representation of JSON request')
    parser.add_argument('--jsonfile', default=None,
                        help='sum the integers (default: find the max)')
    args = parser.parse_args()

    jsondata = None
    if args.jsonstr:
        jsondata = json.loads(args.jsonstr)
    elif args.jsonfile:
        with open(args.jsonfile) as infile:
            jsondata = json.load(infile)
    else:
        print("You must supply either a JSON string or file")
    if jsondata:
        process = parse_request(args.process, jsondata)
        print("Result saved to {}".format(process.output.uri))
