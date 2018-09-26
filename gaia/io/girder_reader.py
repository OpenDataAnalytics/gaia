from __future__ import absolute_import, print_function
import os

from gaia import GaiaException
from gaia.girder_data import GirderDataObject
from gaia.io.gaia_reader import GaiaReader
from gaia.io.girder_interface import GirderInterface
import gaia.formats as formats
# import gaia.types as types


class GirderReader(GaiaReader):
    """
    A specific subclass for reading GDAL files
    """
    def __init__(self, url, *args, **kwargs):
        """
        """
        super(GirderReader, self).__init__(*args, **kwargs)
        self.url = url

    @staticmethod
    def can_read(url, *args, **kwargs):
        girder_scheme = 'girder://'
        if url is not None and url.startswith(girder_scheme):
            result = GirderReader._parse_girder_url(url)
            if result is None:
                return False

            # (else)
            if not GirderInterface.is_initialized():
                raise GaiaException('Cannot read girder object; must first call gaia.use_girder()')

            # Confirm that resource exists on girder?
            # Todo move to GirderDataObject
            # gc = GirderInterface._get_girder_client()
            # resource_type,resource_id = result
            # resource = gc.get('{}/{}'.format(resource_type,resource_id))
            # print('resource:', resource)

            return True

        # (else)
        return False

    def read(self, **kwargs):
        """Returns a GirderDataset

        Doesn't actally load or move data; it remains on Girder
        Todo: kwargs should probably be a union of raster and vector types,
        that get passed to GirderDataset

        :return: Girder Dataset
        """
        parsed_result = self.__class__._parse_girder_url(self.url)
        if parsed_result is None:
            raise GaiaException('Internal error - not a girder url')

        resource_type,resource_id = parsed_result
        return GirderDataObject(self, resource_type, resource_id)

    def load_metadata(self, dataObject):
        # Todo
        pass

    @staticmethod
    def _parse_girder_url(url):
        """

        Returns either None or tuple(resource_type, resource_id)
        """
        if url is None:
            raise GaiaException('Internal error - url is None')

        girder_scheme = 'girder://'
        if not url.startswith(girder_scheme):
            return None

        # Extract resource type (file or folder) and id
        start_index = len(girder_scheme)
        path_string = url[start_index:]
        path_list = path_string.split('/')
        #print('path_list: ', path_list)
        if (len(path_list) != 2):
            raise GaiaException('Invalid girder url; path must be length 2')

        resource_type, resource_id = path_list
        if (resource_type not in ['file', 'folder']):
            raise GaiaException('Invalid girder url; path must start with either "file/" or "folder/"')

        return resource_type,resource_id
