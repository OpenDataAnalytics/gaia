from __future__ import absolute_import, print_function
import os

from gaia import GaiaException
from gaia.io.gaia_reader import GaiaReader
from gaia.io.girder_interface import GirderInterface
import gaia.formats as formats
# import gaia.types as types


class GirderReader(GaiaReader):
    """
    A specific subclass for reading GDAL files
    """
    def __init__(self, *args, **kwargs):
        super(GirderReader, self).__init__(*args, **kwargs)

    @staticmethod
    def can_read(*args, **kwargs):
        uri = kwargs.get('uri')
        #print('kwargs', kwargs)
        girder_scheme = 'girder://'
        if uri is not None and uri.startswith(girder_scheme):
            if not GirderInterface.is_initialized():
                raise GaiaException('Cannot read girder object; must first call gaia.use_girder()')

            # Extract resource type (file or folder) and id
            start_index = len(girder_scheme)
            path_string = uri[start_index:]
            path_list = path_string.split('/')
            #print('path_list: ', path_list)
            if (len(path_list) != 2):
                raise GaiaException('Invalid girder url; path must be length 2')

            resource_type, resource_id = path_list
            if (resource_type not in ['file', 'folder']):
                raise GaiaException('Invalid girder url; path must start with either "file/" or "folder/"')

            # ?Confirm that resource exists on girder?
            gc = GirderInterface._get_girder_client()
            resource = gc.get('{}/{}'.format(resource_type,resource_id))
            print('resource:', resource)

            return True

        # (else)
        return True

    def read(self, **kwargs):
        """Returns a GirderDataset

        Doesn't actally load or move data; it remains on Girder
        Todo: kwargs should probably be a union of raster and vector types,
        that get passed to GirderDataset

        :return: Girder Dataset
        """
        return None

    def load_metadata(self, dataObject):
        # Todo
        pass
