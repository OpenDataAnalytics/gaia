from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

import os

try:
    import osr
except ImportError:
    from osgeo import osr

import gdal
from gaia.geo.gdal_functions import (
    gdal_reproject,
    raster_to_numpy_array,
    rasterio_bbox,
    rasterio_footprint
)

from gaia.io.gaia_reader import GaiaReader
from gaia.gaia_data import GDALDataObject
from gaia.util import (
    UnhandledOperationException,
    UnsupportedFormatException,
    get_uri_extension
)
import gaia.formats as formats
import gaia.types as types


class GaiaGDALReader(GaiaReader):
    """
    A specific subclass for reading GDAL files
    """
    def __init__(self, url, *args, **kwargs):
        super(GaiaGDALReader, self).__init__(*args, **kwargs)

        self.uri = url
        self.ext = '.%s' % get_uri_extension(self.uri)

        self.as_numpy_array = False
        self.as_single_band = True
        self.old_nodata = None
        self.new_nodata = None

    @staticmethod
    def can_read(url, *args, **kwargs):
        # Todo update for girder-hosted files
        if not isinstance(url, str):
            return False

        extension = get_uri_extension(url)
        if extension == 'tif' or extension == 'tiff':
            return True
        return False

    def read(self, format=formats.RASTER, epsg=None, as_numpy_array=False,
             as_single_band=True, old_nodata=None, new_nodata=None):
        """
        Read data from a raster dataset

        :param as_numpy_array: Output data as numpy
        (default is False i.e. raster osgeo.gdal.Dataset)
        :param as_single_band: Output data as 2D array of its first band
        (default is True). If False, returns full 3D array.
        :param old_nodata: Explicitly identify existing NoData values
        (default None). If None, attempts to get existing NoData values stored
        in the raster band.
        :param new_nodata: Replace NoData values in each band with new_nodata
        (default None). If new_nodata is not None but old_nodata is None
        and no existing NoData value is stored in the band, uses unchanged
        default ReadAsArray() return values.
        :param epsg: EPSG code to reproject data to
        :return: GDAL Dataset
        """
        self.format = format
        self.epsg = epsg
        self.as_numpy_array = as_numpy_array
        self.as_single_band = as_single_band
        self.old_nodata = old_nodata
        self.new_nodata = new_nodata

        # FIXME: if we got "as_numpy_array=True", should we return different
        # data object type?
        o = GDALDataObject(reader=self, dataFormat=self.format, epsg=self.epsg)
        return o

    def load_metadata(self, dataObject):
        self.__read_internal(dataObject)

    def load_data(self, dataObject):
        self.__read_internal(dataObject)

    def __read_internal(self, dataObject):
        if self.ext not in formats.RASTER:
            raise UnsupportedFormatException(
                "Only the following raster formats are supported: {}".format(
                    ','.join(formats.RASTER)
                )
            )
        self.basename = os.path.basename(self.uri)

        dataObject.set_data(gdal.Open(self.uri))

        if self.epsg and dataObject.get_epsg() != self.epsg:
            dataObject.reproject(self.epsg)

        dataObject.set_metadata({})
        dataObject._datatype = types.RASTER
        dataObject._dataformat = formats.RASTER

        if self.as_numpy_array:
            raise UnhandledOperationException('Convert GDAL dataset to numpy')
            # np_data = raster_to_numpy_array(out_data, as_single_band,
            #                                 old_nodata, new_nodata)
