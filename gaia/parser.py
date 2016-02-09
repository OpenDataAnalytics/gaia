import argparse
import json
from six import string_types
from gaia.processes import create_process
from gaia.inputs import *


class GaiaRequestParser(object):
    """
    Generate processes and inputs from a JSON object
    :return a GaiaProcess object
    """

    process = None
    data = None

    def __init__(self, process_name, data=None, parse=True, config=None):
        """
        Create an instance of GaiaRequestParser
        """
        self.process = create_process(process_name)
        if data and parse:
            self.parse(data)

    def parse(self, data):
        """
        Generate process and input objects from JSON data
        """
        if isinstance(data, string_types):
            data = json.loads(data)
        process_inputs = data['data_inputs']
        self.process.args = data['args'] if 'args' in data else None
        self.process.inputs = []
        for input in process_inputs:
            io = create_io(input, process_inputs[input])
            self.process.inputs.append(io)
        return self.process


def is_vector(filename):
    try:
        return os.path.splitext(filename)[1] in formats.VECTOR
    except IndexError:
        return False


def create_io(name, data):
    if data['type'] == 'file':
        io = VectorFileIO(name, **data) if is_vector(
            data['uri']) else RasterFileIO(name, **data)
        return io
    elif data['type'] == 'process':
        process_name = data['process']['name']
        parser = GaiaRequestParser(process_name, data=data['process'])
        return ProcessIO(process_name, parser.process)
    # elif data['type'] == 'girder':
    #     return GirderIO(**data)
    # elif data['type'] == 'wfs':

    #     return WfsIO(**data)
    # elif data['type'] == 'wfs':
    #     return WpsIO(**data)
    # elif data['type'] == 'raw':
    #     return GaiaIO(**data)
    # elif data['type'] == 'pg':
    #     return PostgisIO(**data)
    else:
        raise NotImplementedError()


def parse_request(process, request_json):
    """
    Parse a JSON request using GaiaRequestParser
    """
    parser = GaiaRequestParser(process, data=request_json, parse=True)
    parser.process.compute()
    return parser.process.output.data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run geospatial process.')
    parser.add_argument('process')
    parser.add_argument('--jsonstr', default=None,
                        help='String representation of JSON request')
    parser.add_argument('--jsonfile', default=None,
                        help='sum the integers (default: find the max)')
    parser.add_argument('--outfile', default=None,
                        help='Save results to a file')
    args = parser.parse_args()

    jsondata = None
    if args.jsonstr:
        jsondata = json.loads(args.jsonstr)
    elif args.jsonfile:
        with open(args.jsonfile) as infile:
            jsondata = json.load(infile)
    else:
        print "You must supply either a JSON string or file"
    if jsondata:
        result = parse_request(args.process, jsondata)
        if not args.outfile:
            print result
        else:
            with open(args.outfile, 'w') as outfile:
                outfile.write()
            print "Result saved to {}".format(args.outfile)
