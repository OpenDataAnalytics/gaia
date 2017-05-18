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

# import numpy as np
# import gdal
# import gaia.formats as formats
# from gaia.geo.gdal_functions import get_dataset
from gaia.inputs import FileIO


class Converter(FileIO):
    """Abstract class to define a converter."""

    def set_data(*args, **kwargs):
        """
        Abstract method for setting dataset to be converted.
        """
        raise NotImplementedError()

    def get_type(self):
        """
        Abstract method to identify the type of the dataset currently stored.
        """
        raise NotImplementedError()

    def to_vector(*args, **kwargs):
        """
        Abstract method for converting to vector format.

        :param args: Required arguments
        :param kwargs: Keyword arguments
        """
        raise NotImplementedError()

    def to_raster(*args, **kwargs):
        """
        Abstract method for converting to raster format.

        :param args: Required arguments
        :param kwargs: Keyword arguments
        """
        raise NotImplementedError()


class InMemoryConverter(Converter):
    """Convert objects from memory and return as in-memory objects."""

    def set_data(dataset):
        """
        Set the dataset to be converted if not identified when initializing.
        """
        # TODO: use similar handling as FileIO
        raise NotImplementedError()

    def get_type(self):
        """
        Identify the type of the dataset currently stored.
        """
        # TODO:
        raise NotImplementedError()

    def to_vector(self):
        """
        Convert to vector dataset.

        :param raster_in: raster input dataset
        :return: vector output dataset
        """
        # TODO: use gdal.Polygonize and see sample code at
        # https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.
        # html#polygonize-a-raster-band
        raise NotImplementedError()

    def to_raster(self):
        """
        Convert to raster dataset.

        :param vector_in: vector input dataset
        :return: raster output dataset
        """
        # TODO: use gdal.RasterizeLayer and see sample code at
        # https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.
        # html#convert-an-ogr-file-to-a-raster
        raise NotImplementedError()

    def to_numpy(self, as_single_band=True, old_nodata=None, new_nodata=None):
        """
        Convert to numpy dataset.

        :param as_single_band: Output data as 2D array of its first band
        (default is True). If False, returns full 3D array.
        :param old_nodata: Explicitly identify existing NoData values
        (default None). If None, attempts to get existing NoData values stored
        in the raster band.
        :param new_nodata: Replace NoData values in each band with new_nodata
        (default None). If new_nodata is not None but old_nodata is None
        and no existing NoData value is stored in the band, uses unchanged
        default ReadAsArray() return values.
        :return: Converted numpy array dataset
        """
        # TODO: see raster_to_numpy_array support in
        # Issue 84: Raster to NumPy Array Support
        raise NotImplementedError()


class ReadWriteConverter(InMemoryConverter):
    """Convert objects from disk and write objects to disk."""

    def set_data(uri):
        """
        Set the dataset to be converted if not identified when initializing.
        """
        # TODO: use similar handling as FileIO
        raise NotImplementedError()

    def get_type(self):
        """
        Identify the type of the dataset currently stored.
        """
        # TODO:
        raise NotImplementedError()

    def to_vector(self, out_path):
        """
        Convert to a vector file and write to disk.

        :param out_path: vector output filepath
        """
        # TODO: use gdal.Polygonize and see sample code at
        # https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.
        # html#polygonize-a-raster-band
        # Handle both vector to vector and raster to vector conversions.
        # Use potential call to get_type select which I/O write driver
        # should be used (between raster and vector).
        raise NotImplementedError()

    def to_raster(self, out_path):
        """
        Convert to a raster file and write to disk.

        :param out_path: raster output filepath
        """
        # TODO: use gdal.RasterizeLayer and see sample code at
        # https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.
        # html#convert-an-ogr-file-to-a-raster
        # Handle both vector to raster and raster to raster conversions.
        # Use potential call to get_type select which I/O write driver
        # should be used (between raster and vector).
        raise NotImplementedError()
