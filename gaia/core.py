import ConfigParser
import json
import os
import shutil
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


if __name__ == '__main__':
    test_dir = '../plugin_tests/data/geoprocess'
    with open(os.path.join(base_dir,
              '{}/within_nested_buffer_process.json'.format(test_dir))) as inf:
        json_string = inf.read().replace(
            '{basepath}', os.path.abspath(os.path.join(base_dir, test_dir)))
    jsondata = json.loads(json_string)
    grp = GaiaRequestParser('within', jsondata)
    grp.process.calculate()
    print grp.process.output
