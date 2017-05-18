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

import numpy as np
# import gdal
# import gaia.formats as formats
# from gaia.geo.gdal_functions import get_dataset


class Converter(object):
    """Abstract class to define a converter."""

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
    """Convert objects from memory and return as in-memory objects."""

    def raster_to_vector(raster_in):
        """
        Convert a raster dataset into a vector dataset.

        :param raster_in: raster input dataset
        :return: vector output dataset
        """
        raise NotImplementedError()

    def vector_to_raster(vector_in):
        """
        Convert a vector dataset into a raster dataset.

        :param vector_in: vector input dataset
        :return: raster output dataset
        """
        raise NotImplementedError()

    def raster_to_numpy(raster_in, as_single_band=True,
                        old_nodata=None, new_nodata=None):
        """
        Convert raster dataset to numpy dataset.

        :param raster_in: Original raster input dataset
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
        bands = as_single_band + (1 - as_single_band) * raster_in.RasterCount
        nrow = raster_in.RasterYSize
        ncol = raster_in.RasterXSize
        dims = (bands, nrow, ncol)

        out_data_array = np.full(dims, np.nan)

        for i in range(bands):
            srcband = raster_in.GetRasterBand(i + 1)
            srcband_array = np.array(srcband.ReadAsArray().astype(np.float))
            if old_nodata is None:
                old_nodata = srcband.GetNoDataValue()
            if new_nodata is not None and old_nodata is not None:
                if np.isnan(old_nodata):
                    srcband_array[np.isnan(srcband_array)] = new_nodata
                else:
                    srcband_array[srcband_array == old_nodata] = new_nodata
                print('NoData: Replaced ' + str(old_nodata) +
                      ' with ' + str(new_nodata))
            out_data_array[i, :, :] = srcband_array

        if as_single_band:
            return out_data_array[0, :, :]
        else:
            return out_data_array

    def vector_to_numpy(vector_in):
        """
        Convert vector dataset to numpy dataset.

        :param vector_in: vector input dataset
        :return: numpy array output dataset
        """
        raise NotImplementedError()


class ReadWriteConverter(Converter):
    """Convert objects from disk and write objects to disk."""

    def raster_to_vector(raster_in, vector_out):
        """
        Convert a raster file into a vector file on disk.

        :param raster_in: raster input filepath
        :param vector_out: vector output filepath
        """
        raise NotImplementedError()

    def vector_to_raster(vector_in, raster_out):
        """
        Convert a vector file into a raster file on disk.

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
