from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

#from gaia import GaiaException
from gaia.gaia_data import GaiaDataObject
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
            metadata = gc.get('item/{}/geometa'.format(self.resource_id))
            self._metadata = metadata
        return self._metadata

    def _get_tiles_url(self):
        """Constructs url for large_image display

        Returns None for non-raster datasets
        """
        if self._getdatatype() != 'raster':
            return None

        # (else)
        girder_url = GirderInterface.get_instance().girder_url
        tile_url = '{}/{}/{{z}}/{{y}}/{{x}}'.format(girder_url, self.resource_id)
        print('Using tile_url:', tile_url)
        return tile_url
