from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

import re
import geopandas

from gaia.io.readers import GaiaReader
from gaia.gaia_data import GaiaDataObject
from gaia import GaiaException
from gaia.util import (
    MissingParameterError,
    MissingDataException,
    UnsupportedFormatException,
    get_uri_extension
)
import gaia.formats as formats
import gaia.types as types


class GaiaGeoJSONReader(GaiaReader):
    """
    Another specific subclass for reading GeoJSON
    """
    epsgRegex = re.compile('epsg:([\d]+)')

    def __init__(self, url, *args, **kwargs):
        super(GaiaGeoJSONReader, self).__init__(*args, **kwargs)

        self.uri = url
        self.ext = '.%s' % get_uri_extension(self.uri)

    @staticmethod
    def can_read(url, *args, **kwargs):
        # Todo update for girder-hosted files
        if not isinstance(url, str):
            return False

        extension = get_uri_extension(url)
        if extension == 'geojson':
            return True
        return False

    def read(self, format=None, epsg=None):
        return super().read(format, epsg)

    def load_metadata(self, dataObject):
        self.__read_internal(dataObject)

    def load_data(self, dataObject):
        self.__read_internal(dataObject)

    def __read_internal(self, dataObject):
        # FIXME: need to handle format
        # if not self.format:
        #     self.format = self.default_output

        # FIXME: Should this check actually go into the can_read method?
        if self.ext not in formats.VECTOR:
            raise UnsupportedFormatException(
                "Only the following vector formats are supported: {}".format(
                    ','.join(formats.VECTOR)
                )
            )

        data = geopandas.read_file(self.uri)

        # FIXME: still need to handle filtering
        # if self.filters:
        #     self.filter_data()

        # FIXME: skipped the transformation step for now
        # return self.transform_data(format, epsg)

        # do the actual reading and set both data and metadata
        # on the dataObject parameter

        # Initialize metadata
        metadata = dict()

        # Calculate bounds
        feature_bounds = data.bounds
        minx = feature_bounds['minx'].min()
        miny = feature_bounds['miny'].min()
        maxx = feature_bounds['maxx'].max()
        maxy = feature_bounds['maxy'].max()

        # Hack format to match resonant geodata (geojson polygon)
        coords = [[
            [minx, miny], [], [maxx, maxy], []
        ]]
        metadata['bounds'] = dict(coordinates=coords)

        dataObject.set_metadata(metadata)


        dataObject.set_data(data)
        epsgString = data.crs['init']
        m = self.epsgRegex.search(epsgString)
        if m:
            dataObject._epsg = int(m.group(1))
        dataObject._datatype = types.VECTOR
        dataObject._dataformat = formats.VECTOR
