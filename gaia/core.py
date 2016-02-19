try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser
import os
import shutil

base_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)))


class GaiaException(Exception):
    """
    Base Gaia exception class
    """
    pass


def get_abspath(inpath):
    """
    Get absolute path of a path string
    :param inpath: file path string
    :return: absolute path as string
    """
    if not os.path.isabs(inpath):
        return os.path.abspath(os.path.join(base_dir, inpath))


def get_config():
    """
    Retrieve app configuration parameters
    such as database connections
    :return: configuration
    """
    config_file = os.path.join(base_dir, 'conf/gaia.local.cfg')
    if not os.path.exists(config_file):
        shutil.copy(config_file.replace('local', 'dist'), config_file)
    parser = ConfigParser()
    parser.read(config_file)
    config_dict = {}
    for section in parser.sections():
        config_dict[section] = {}
        for key, val in parser.items(section):
            config_dict[section][key] = val
    return config_dict


config = get_config()
