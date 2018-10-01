from __future__ import print_function
from future.standard_library import install_aliases

import girder_client

from gaia.util import MissingParameterError


class GirderInterface(object):
    """An internal class that provides a thin encapsulation of girder_client.

    This class must be sued as a singleton.
    """

    instance = None  # singleton

    def __init__(self):
        """Applies crude singleton pattern (raise exception if called twice)
        """
        if GirderInterface.instance:
            raise Exception('GirderInterface already exists -- use get_instance() class method')

        GirderInterface.instance = self
        self.gc = None  # girder client
        self.user = None  # girder user object

    @classmethod
    def get_instance(cls):
        """Returns singleton instance, creating if needed.
        """
        if cls.instance is None:
            cls.instance = cls()

        return cls.instance

    @classmethod
    def is_initialized(cls):
        if cls.instance is None:
            return False

        if cls.instance.gc is None:
            return False

        # (else)
        return True

    def initialize(self, girder_url, username=None, password=None, apikey=None):
        """Connect to girder server and authenticate with input credentials

        :param girder_url: The full path to the Girder instance, for example,
        'http://localhost:80' or 'https://my.girder.com'.
        :param username: The name for logging into Girder.
        :param password: The password for logging into Girder.
        :apikey: An api key, which can be used instead of username & password.
        """
        if self.__class__.is_initialized():
            raise GaiaException('GirderInterface already initialized -- cannot initialize twice')

        # Check that we have credentials

        api_url = '{}/api/v1'.format(girder_url)
        #print('api_url: {}'.format(api_url))
        gc = girder_client.GirderClient(apiUrl=api_url)
        #gc = girder_client.GirderClient(apiUrl='https://data.kitware.com/api/v1')

        if username is not None and password is not None:
            gc.authenticate(username=username, password=password)
        elif apikey is not None:
            gc.authenticate(apiKey=apikey)
        else:
            raise MissingParameterError('No girder credentials provided.')

        # Get user info
        self.user = gc.getUser('me')

        # Todo create Private/Gaia folder?

        self.gc = gc

    def lookup_url(self, path, test=False):
        """Returns internal url for resource at specified path

        :param path: (string) Girder path, from user's root to resource
        :param test: (boolean) if True, raise exception if resource not found
        """
        resource = self.lookup_resource(path, test)
        if resource is None:
            return None

        # (else) construct "gaia" url
        resource_type = resource['_modelType']
        resource_id = resource['_id']
        gaia_url = 'girder://{}/{}'.format(resource_type, resource_id)
        return gaia_url



    def lookup_resource(self, path, test=True):
        """Does lookup of resource at specified path

        :param path: (string) Girder path, from user's root to resource
        :param test: (boolean) if True, raise exception if resource not found
        """
        gc = self.__class__._get_girder_client()
        girder_path = 'user/{}/{}'.format(self.user['login'], path)
        resource = gc.get('resource/lookup', parameters={'path': girder_path, 'test': test})
        return resource


    @classmethod
    def _get_girder_client(cls):
        """Returns GirderClient instance

        For internal use only
        """
        if cls.instance is None:
            raise GaiaException('GirderClient not initialized')

        if cls.instance.gc is None:
            raise GaiaException('GirderClient not initialized')

        return cls.instance.gc

