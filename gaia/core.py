import ConfigParser
import os
import shutil

base_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)))


class GaiaException(Exception):
    """
    Base Gaia exception class
    """
    pass


class GaiaConfiguration(object):
    """
    Retrieve app configuration parameters
    such as database connections
    :return: configuration
    """

    def __init__(self):
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
        self.config = config_dict


config = GaiaConfiguration().config
