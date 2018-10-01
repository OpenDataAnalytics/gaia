#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
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
##############################################################################
import importlib
import traceback

import os
import pkg_resources as pr
import logging

from .display import geojs

#: Global version number for the package
__version__ = '0.0.1a1'


try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

logger = logging.getLogger(__name__)

base_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)))

#: Holder for database connection settings
sqlengines = {}

#: Holder for Gaia settings
config = {}


class GaiaException(Exception):
    """
    Base Gaia exception class
    """
    pass


def connect(girder_url='http://localhost:8989', username=None, password=None, apikey=None):
    """Initialize a connection to a Girder data management system

    Gaia datasets can be created from girder files and folders using
    either of these formats:

      gaia.create('girder://file/${id}')
      gaia.create('girder://folder/${id}')

    The datasets are stored in the girder system, and proxied to gaia.

    :param girder_url: The full path to the Girder instance, for example,
    'http://localhost:80' or 'https://my.girder.com'.
    :param username: (string) The name for logging into Girder.
    :param password: (string) The password for logging into Girder.
    :apikey: (string)An api key, which can be used instead of username & password.

    Note that applications can connect to only ONE girder instance for the
    entire session.
    """
    from gaia.io import GirderInterface
    gint = GirderInterface.get_instance()
    if gint.is_initialized():
        raise GaiaException('GirderInterface already initialized.')
    gint.initialize(girder_url, username=username, password=password, apikey=apikey)
    return gint

def create(data_source, *args, **kwargs):
    """
    Convenience method to provide a simpler API for creating
    GaiaDataObject

    :param data_source: the source data for the object. Can be one of:
      * a path (string) on local filesystem
      * a web url (string) that Gaia can download from
      * a python object (numpy array, GeoPandas dataframe, etc.)
      * TBD a tuple indicating postgis parameters
      * a 2-tuple specifying a GirderInterface object and path(string) to the file
    :return: Gaia data obkject
    """
    from gaia.io import readers
    reader = readers.GaiaReader(data_source, *args, **kwargs)
    return reader.read()


def get_abspath(inpath):
    """
    Get absolute path of a path string

    :param inpath: file path string
    :return: absolute path as string
    """
    if not os.path.isabs(inpath):
        return os.path.abspath(os.path.join(base_dir, inpath))
    else:
        return inpath


def get_config(config_file=None):
    """
    Retrieve app configuration parameters
    such as database connections

    :return: configuration
    """
    global config
    if not config_file:
        if config:
            return config
        config_file = os.path.join(base_dir, 'conf/gaia.cfg')
    parser = ConfigParser()
    parser.read(config_file)
    config_dict = {}
    for section in parser.sections():
        config_dict[section] = {}
        for key, val in parser.items(section):
            config_dict[section][key] = val.strip('"').strip("'")
    config = config_dict
    return config_dict

def get_datastore_url(path):
    """Returns url (string) pointing to resource on remote datastore.

    Returns None if the file is not found at the given path.
    """



def get_plugins():
    """
    Load and return a list of installed plugin modules

    :return: list of plugin modules
    """
    installed_plugins = []
    for ep in pr.iter_entry_points(group='gaia.plugins'):
        try:
            module = ep.load()
            importlib.import_module(module.__name__)
            installed_plugins.append(module)
            if hasattr(module, 'get_config'):
                config.update(module.get_config())
        except ImportError:
            logger.error('Could not load module: {}'.format(
                traceback.print_exc()))
    return installed_plugins


def show(*data_objects, **options):
    """
    Displays data objects using available rendering code

    :param data_objects: 1 or more GeoData objects
    :param options: options to pass to rendering backend

    Note: gaia.show() only renders if it is the
    last line of code in the cell input.
    """
    if not data_objects:
        print('(no data objects)')
        return None

    # Is jupyterlab_geojs available?
    if geojs.is_loaded():
        scene = geojs.show(*data_objects, options=options)
        return scene

    # (else)
    print(data_objects)
    return None

get_config()
