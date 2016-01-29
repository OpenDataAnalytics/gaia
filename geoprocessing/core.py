import ConfigParser
import json
import os
import shutil
from six import string_types
import geoprocessing.inputs
import geoprocessing.processes

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
            geoprocessing.core.CONFIG = config
        self.process = geoprocessing.processes.base.create_process(process_name)
        if data and parse:
            self.parse(data)

    def parse(self, data):
        if isinstance(data, string_types):
            data = json.loads(data)
        inputs = data['data_inputs']
        self.process.inputs = []
        for input in inputs:
            gi = geoprocessing.inputs.base.GaiaInput(input)
            gi.io = geoprocessing.inputs.base.create_io(inputs[input])
            self.process.inputs.append(gi)
        return self.process


def getConfig():
    """
    Retrieve app configuration parameters
    such as database connections
    :return: configuration
    """
    if geoprocessing.core.CONFIG is None:
        config_file = os.path.join(base_dir, 'conf/geoprocessing.local.cfg')
        if not os.path.exists(config_file):
            shutil.copy(config_file.replace('local', 'dist'), config_file)
        parser = ConfigParser.ConfigParser()
        parser.read(config_file)
        config_dict = {}
        for section in parser.sections():
            config_dict[section] = {}
            for key, val in parser.items(section):
                config_dict[section][key] = val
        geoprocessing.core.CONFIG = config_dict
    return geoprocessing.core.CONFIG
