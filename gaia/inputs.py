#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
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
###############################################################################
import json
import os
import errno
import fiona
import pysal
import geopandas

import webbrowser
import carmen

import gdal
import shutil
from sqlalchemy import create_engine, MetaData, Table, text
from geoalchemy2 import Geometry

try:
    import osr
except ImportError:
    from osgeo import osr
import gaia.formats as formats


from gaia.core import GaiaException, config, sqlengines, get_abspath
from gaia.filters import filter_pandas, filter_postgis
from rauth import OAuth1Service
from geopy.geocoders import Nominatim
from geopandas import GeoDataFrame
geolocator = Nominatim()


class MissingParameterError(GaiaException):
    """Raise when a required parameter is missing"""
    pass


class MissingDataException(GaiaException):
    """Raise when required data is missing"""
    pass


class UnsupportedFormatException(GaiaException):
    """Raise when an unsupported data format is used"""
    pass


class GaiaIO(object):
    """Abstract IO class for importing/exporting data from a certain source"""
    data = None
    filters = None
    default_output = None

    def __init__(self, **kwargs):
        """
        Create a GaiaIO object, assigning attributes based on kwargs
        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    def read(self, *args, **kwargs):
        """
        Abstract class for reading data, not implemented here
        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def write(self, *args, **kwargs):
        """
        Abstract class for writing data
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def create_output_dir(self, filepath):
        """
        Create an output directory if it doesn't exist
        :param filepath: Directory to create
        :return:
        """
        if not os.path.exists(os.path.dirname(filepath)):
            try:
                os.makedirs(os.path.dirname(filepath))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise

    def get_epsg(self):
        """
        Get the EPSG code of the data
        :return: EPSG code (integer)
        """
        if self.data is None:
            self.read()
        if self.data.__class__.__name__ == 'GeoDataFrame':
            if self.data.crs is None:
                # Assume EPSG:4326
                self.data.crs = fiona.crs.from_epsg(4326)
                self.epsg = 4326
                return self.epsg
            else:
                crs = self.data.crs.get('init', None)
                if crs and ':' in crs:
                    crs = crs.split(':')[1]
                if crs.isdigit():
                    self.epsg = crs
                    return self.epsg
                else:
                    # Assume EPSG:4326
                    self.epsg = 4326
                    self.data.crs = fiona.crs.from_epsg(4326)
                    return self.epsg
        elif self.data.__class__.__name__ == 'Dataset':
            projection = self.data.GetProjection()
            data_crs = osr.SpatialReference(wkt=projection)
            try:
                self.epsg = data_crs.GetAttrValue('AUTHORITY', 1)
                return self.epsg
            except KeyError:
                # Return the WKT projection instead
                self.epsg = projection
                return projection

    def delete(self):
        """
        Abstract class for deleting the IO source
        :return:
        """
        raise NotImplementedError()


class FileIO(GaiaIO):
    """Abstract class to read and write file data."""

    def __init__(self, uri='', **kwargs):
        """
        :param uri: Filepath of IO object
        :param kwargs:
        :return:
        """
        if uri and not self.allowed_folder(uri):
            raise GaiaException(
                "Access to this directory is not permitted : {}".format(
                    os.path.dirname(uri)))
        self.uri = uri
        super(FileIO, self).__init__(uri=uri, **kwargs)
        if self.uri:
            self.ext = os.path.splitext(self.uri)[1].lower()

    def allowed_folder(self, folder):
        """
        Return true or false if folder is in list of
        allowed folders from config
        :param folder: folder to check
        :return: True or False
        """
        allowed_dirs = config['gaia']['fileio_paths'].split(',')
        if not allowed_dirs[0]:
            return True
        filepath = os.path.abspath(os.path.dirname(folder))
        allowed = False
        for path in allowed_dirs:
            if filepath.startswith(get_abspath(path)):
                allowed = True
                break
        return allowed

    def delete(self):
        """
        Remove file of IO object
        :return:
        """
        if os.path.exists(self.uri):
            shutil.rmtree(os.path.dirname(self.uri))


class GirderIO(GaiaIO):
    """Read and write Girder files/items/metadata"""

    default_output = None

    def __init__(self, name, girder_uris=[], auth=None, **kwargs):
        super(GirderIO, self).__init__(**kwargs)
        raise NotImplementedError


class JsonFileIO(FileIO):
    """Read json and write json file data (such as .json)"""

    default_output = formats.JSON

    def read(self, format=None):
        if not format:
            format = self.default_output
        if self.ext not in formats.JSON:
            raise UnsupportedFormatException(
                "Only the following weight formats are supported: {}".format(
                    ','.join(formats.JSON)
                )
            )
        if self.data is None:
            with open(self.uri, 'r') as f:
                self.data = json.load(f)
        return self.data

    def write(self, filename=None, as_type='json'):
        """
        Write data (assumed dictionary object) to json file
        :param filename: Base filename
        :param as_type: json
        :return: location of file
        """
        if not filename:
            filename = self.uri
        self.create_output_dir(filename)
        if as_type == 'json':
            with open(filename, 'w') as f:
                json.dump(self.data, f)
        else:
            raise NotImplementedError('{} not a valid type'.format(as_type))
        return self.uri
