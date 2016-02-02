import ConfigParser
import json
import os
import shutil
import argparse
from six import string_types
import gaia.inputs
import gaia.processes

base_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)))

CONFIG = None

class GaiaException(Exception):
    pass


class GaiaRequestParser(object):
    """
    Generate processes and inputs from a JSON object
    :return a GaiaProcess object
    """

    process = None
    data = None

    def __init__(self, process_name, data=None, parse=True, config=None):
        if config:
            gaia.core.CONFIG = config
        self.process = gaia.processes.base.create_process(process_name)
        if data and parse:
            self.parse(data)

    def parse(self, data):
        if isinstance(data, string_types):
            data = json.loads(data)
        inputs = data['data_inputs']
        self.process.args = data['args'] if 'args' in data else None
        self.process.inputs = []
        for input in inputs:
            gi = gaia.inputs.base.GaiaInput(input)
            gi.io = gaia.inputs.base.create_io(inputs[input])
            self.process.inputs.append(gi)
        return self.process


def getConfig():
    """
    Retrieve app configuration parameters
    such as database connections
    :return: configuration
    """
    if gaia.core.CONFIG is None:
        config_file = os.path.join(base_dir, 'conf/gaia.local.cfg')
        if not os.path.exists(config_file):
            shutil.copy(config_file.replace('local', 'dist'), config_file)
        parser = ConfigParser.ConfigParser()
        parser.read(config_file)
        config_dict = {}
        for section in parser.sections():
            config_dict[section] = {}
            for key, val in parser.items(section):
                config_dict[section][key] = val
        gaia.core.CONFIG = config_dict
    return gaia.core.CONFIG


def parse_request(process, request_json):
    parser  = GaiaRequestParser(process, data=request_json, parse=True)
    parser.process.calculate()
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
