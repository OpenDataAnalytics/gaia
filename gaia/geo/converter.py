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

import gdal
import gaia.formats as formats
from gaia.geo.gdal_functions import get_dataset

class Converter(object):
    """
    Abstract class to define a converter.
    """

    def raster_to_vector(*args, **kwargs):
        """
        Abstract method for converting between raster and vector.

        :param args: Required arguments
        :param kwargs: Keyword arguments
        """
        raise NotImplementedError()


    def vector_to_raster(*args, **kwargs):
        """
        Abstract method for converting between vector and raster.

        :param args: Required arguments
        :param kwargs: Keyword arguments
        """
        raise NotImplementedError()

class InMemoryConverter(Converter):
    """
    Convert objects from either memory or disk and
    return as in-memory objects.
    """

    def raster_to_vector(raster_in):
        """
        Convert a raster file into a vector file.

        :param raster_in: raster input dataset
        :return: vector output dataset
        """
        raise NotImplementedError()


    def vector_to_raster(vector_in):
        """
        Convert a vector file into a raster file.

        :param vector_in: vector input dataset
        :return: raster output dataset
        """
        raise NotImplementedError()


    def raster_to_numpy(raster_in):
        """
        Convert raster output to numpy array output.

        :param raster_in: raster input dataset
        :return: numpy array output dataset
        """
        raise NotImplementedError()


    def vector_to_numpy(vector_in):
        """
        Convert vector output to numpy array output.

        :param vector_in: vector input dataset
        :return: numpy array output dataset
        """
        raise NotImplementedError()

class ReadWriteConverter(Converter):
    """
    Convert objects from disk and write objects to disk.
    Covers conversions between file formats e.g., JPEG to PNG.
    """

    def raster_to_vector(raster_in, vector_out):
        """
        Convert a raster file into a polygonized vector file on disk.

        :param raster_in: raster input filepath
        :param vector_out: vector output filepath
        """
        raise NotImplementedError()


    def vector_to_raster(vector_in, raster_out):
        """
        Rasterize a vector file into a raster file on disk.

        :param vector_in: vector input filepath
        :param raster_out: raster output filepath
        """
        raise NotImplementedError()


    def raster_to_raster(raster_in, raster_out):
        """
        Convert between raster file formats on disk.

        :param raster_in: raster input filepath
        :param raster_out: raster output filepath
        """
        raise NotImplementedError()


    def vector_to_vector(vector_in, vector_out):
        """
        Convert between vector file formats on disk.

        :param raster_in: raster input filepath
        :param raster_out: raster output filepath
        """
        raise NotImplementedError()
