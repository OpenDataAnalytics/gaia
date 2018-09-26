from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

#from gaia import GaiaException
from gaia.gaia_data import GaiaDataObject, GaiaException
from gaia.io.girder_interface import GirderInterface


class GirderDataObject(GaiaDataObject):
    """Proxies either a file or a folder on girder

    """
    def __init__(self, reader, resource_type, resource_id, **kwargs):
        super(GirderDataObject, self).__init__(**kwargs)
        self._reader = reader
        self.resource_type = resource_type
        self.resource_id = resource_id

    def get_metadata(self, force=False):
        if force or self._metadata is None:
            gc = GirderInterface._get_girder_client()
            metadata = gc.get('{}/{}'.format(self.resource_type,self.resource_id))
            self._metadata = metadata
        return self._metadata
