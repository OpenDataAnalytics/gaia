from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from gaia.gaia_data import PostgisDataObject
from gaia.io.readers import GaiaReader

import gaia.types as types
import gaia.formats as formats


class GaiaPostGISReader(GaiaReader):
    required_arguments = ['table', 'dbname', 'hostname', 'user', 'password']

    def __init__(self, *args, **kwargs):
        super(GaiaPostGISReader, self).__init__(*args, **kwargs)
        self._args = args
        self._kwargs = kwargs

    def read(self, format=None, epsg=None):
        print('GaiaPostGISReader read()')
        dataObject = PostgisDataObject(reader=self)
        dataObject.format = format
        dataObject.epsg = epsg
        return dataObject

    def load_metadata(self, dataObject):
        self.__set_db_properties(dataObject)

    def load_data(self, dataObject):
        self.__set_db_properties(dataObject)

    def __set_db_properties(self, dataObject):
        for key in self.required_arguments:
            if key in self._kwargs:
                print('  Setting property %s to %s' % (key, self._kwargs[key]))
                setattr(dataObject, key, self._kwargs[key])
        dataObject.initialize_engine()
        dataObject.datatype = types.VECTOR
        dataObject.dataformat = formats.VECTOR

    @staticmethod
    def can_read(*args, **kwargs):
        for arg in GaiaPostGISReader.required_arguments:
            if arg not in kwargs:
                return False
        return True
