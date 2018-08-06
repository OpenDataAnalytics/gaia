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


def create(*args, **kwargs):
    """
    Convenience method to provide a simpler API for creating
    GaiaDataObject
    """
    from gaia.io import readers
    reader = readers.GaiaReader(*args, **kwargs)
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


get_config()

def show(*data_objects):
    """
    Displays data objects using available rendering code

    :param data_object: 1 or more GeoData objects
    """
    if not data_objects:
        print('(no data objects)')
        return

    # Is jupyterlab_geojs available?
    try:
        import json
        from IPython.display import display
        import jupyterlab_geojs
    except ImportError as err:
        print(data_objects)
        return

    # (else)
    #print(data_objects)
    scene = jupyterlab_geojs.Scene()
    scene.create_layer('osm')
    feature_layer = scene.create_layer('feature')

    combined_bounds = None
    # Reverse order so that first item ends on top
    for data_object in reversed(data_objects):
        # Create map feature
        #print(data_object._getdatatype(), data_object._getdataformat())
        # type is vector, format is [.json, .geojson, .shp, pandas]
        data = data_object.get_data()

        # Can only seem to get json *string*; so parse into json *object*
        json_string = data.to_json()
        json_object = json.loads(json_string)
        feature = feature_layer.create_feature('geojson', json_object)
        #print(json_object)
        feature.enableToolTip = True  # dont work

        geometry = data['geometry']
        bounds = geometry.total_bounds
        #print(bounds)
        if combined_bounds is None:
            combined_bounds = bounds
        else:
            combined_bounds[0] = min(combined_bounds[0], bounds[0])
            combined_bounds[1] = min(combined_bounds[1], bounds[1])
            combined_bounds[2] = max(combined_bounds[2], bounds[2])
            combined_bounds[3] = max(combined_bounds[3], bounds[3])

    #print(combined_bounds)
    corners = [
        [combined_bounds[0], combined_bounds[1]],
        [combined_bounds[2], combined_bounds[1]],
        [combined_bounds[2], combined_bounds[3]],
        [combined_bounds[0], combined_bounds[3]]
    ]
    scene.set_zoom_and_center(corners=corners)
    display(scene)
