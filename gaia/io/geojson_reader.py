from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

import re
from six import string_types
import geojson
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

    def __init__(self, data_source, *args, **kwargs):
        super(GaiaGeoJSONReader, self).__init__(*args, **kwargs)

        self.geojson_object = None
        self.uri = None
        self.ext = None

        if isinstance(data_source, string_types):
            self.uri = data_source
            self.ext = '.%s' % get_uri_extension(self.uri)
        elif isinstance(data_source, geojson.GeoJSON):
            self.geojson_object = data_source

    @staticmethod
    def can_read(data_source, *args, **kwargs):
        if isinstance(data_source, string_types):
            # Check string for a supported filename/url
            extension = '.{}'.format(get_uri_extension(data_source))
            if extension in formats.VECTOR:
                return True
            return False
        elif isinstance(data_source, geojson.GeoJSON):
            return True

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

        if self.uri:
            if self.ext not in formats.VECTOR:
                tpl = "Only the following vector formats are supported: {}"
                msg = tpl.format(','.join(formats.VECTOR))
                raise UnsupportedFormatException(msg)
            data = geopandas.read_file(self.uri)

        elif self.geojson_object:
            if isinstance(self.geojson_object, geojson.geometry.Geometry):
                feature = geojson.Feature(geometry=self.geojson_object)
                features = geojson.FeatureCollection([feature])
            elif isinstance(self.geojson_object, geojson.Feature):
                features = geojson.FeatureCollection([self.geojson_object])
            elif isinstance(self.geojson_object, geojson.FeatureCollection):
                features = self.geojson_object
            else:
                raise UnsupportedFormatException(
                    'Unrecognized geojson object {}'.self.geojson_object)

            # For now, hard code crs to lat-lon
            data = geopandas.GeoDataFrame.from_features(
                features, crs=dict(init='epsg:4326'))

        # FIXME: still need to handle filtering
        # if self.filters:
        #     self.filter_data()

        # FIXME: skipped the transformation step for now
        # return self.transform_data(format, epsg)

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
