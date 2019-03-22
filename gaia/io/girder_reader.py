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
    def __init__(self, data_source, *args, **kwargs):
        """
        """
        super(GirderReader, self).__init__(*args, **kwargs)
        self.girder_source = data_source
        self.url = None
        # Bounds can be pass in optionally
        self.bounds = kwargs.get('bounds')

        if isinstance(data_source, str):
            self.url = data_source
        elif isinstance(data_source, tuple):
            self.girder_source = data_source

    @staticmethod
    def can_read(source, *args, **kwargs):
        # For now, support either url (string) or tuple (GirderInterface,path)
        if isinstance(source, str):
            girder_scheme = 'girder://'
            if source is not None and source.startswith(girder_scheme):
                result = GirderReader._parse_girder_url(source)
                if result is None:
                    return False

                # Todo Confirm that resource exists on girder?
                return True

            # (else)
            return False
        else:
            if not isinstance(source, tuple) or not len(source) == 2:
                return False

            gint, path = source
            if not isinstance(gint, GirderInterface):
                return False

            if not isinstance(path, str):
                raise GaiaException('Second tuple element is not a string')

            if not gint.is_initialized():
                msg = """Cannot read girder object; \
                    must first call gaia.connect()"""
                raise GaiaException(msg)

        # (else)
        return True

    def read(self, **kwargs):
        """Returns a GirderDataset

        Doesn't actally load or move data; it remains on Girder
        Todo: kwargs should probably be a union of raster and vector types,
        that get passed to GirderDataset

        :return: Girder Dataset
        """
        if self.url:
            parsed_result = self.__class__._parse_girder_url(self.url)
            if parsed_result is None:
                raise GaiaException('Internal error - not a girder url')

            resource_type, resource_id = parsed_result
            return GirderDataObject(
                self, resource_type, resource_id, bounds=self.bounds)

        elif self.girder_source:
            gint, path = self.girder_source
            resource = gint.lookup_resource(path)
            if resource is None:
                template = 'File not found on Girder at specified path ({})'
                msg = template.format(path)
                raise GaiaException(msg)

            resource_type = resource['_modelType']
            resource_id = resource['_id']
            return GirderDataObject(
                self, resource_type, resource_id, bounds=self.bounds)

        raise GaiaException(
            'Internal error - should never reach end of GirderReader.read()')
        return None

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
        # print('path_list: ', path_list)
        if (len(path_list) != 2):
            raise GaiaException('Invalid girder url; path must be length 2')

        resource_type, resource_id = path_list
        if (resource_type not in ['item', 'folder']):
            msg = """Invalid girder url; path must start with either \
                \"item/\" or \"folder/\""""
            raise GaiaException(msg)

        return resource_type, resource_id
