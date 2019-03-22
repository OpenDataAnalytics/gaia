from __future__ import print_function

import requests

import girder_client

from gaia.util import GaiaException, MissingParameterError


class GirderInterface(object):
    """An internal class that provides a thin encapsulation of girder_client.

    This class must be used as a singleton.
    """

    instance = None  # singleton

    def __init__(self):
        """Applies crude singleton pattern (raise exception if called twice)
        """
        if GirderInterface.instance:
            msg = """GirderInterface already exists \
            -- use get_instance() class method"""
            raise GaiaException(msg)

        GirderInterface.instance = self
        self.girder_url = None
        self.gc = None  # girder client
        self.user = None  # girder user object
        self.gaia_folder = None
        self.default_folder = None
        self.nersc_requests = None  # requests session

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

    def initialize(
            self,
            girder_url,
            username=None,
            password=None,
            apikey=None,
            newt_sessionid=None):
        """Connect to girder server and authenticate with input credentials

        :param girder_url: The full path to the Girder instance, for example,
        'http://localhost:80' or 'https://my.girder.com'.
        :param username: The name for logging into Girder.
        :param password: The password for logging into Girder.
        :apikey: An api key, which can be used instead of username & password.
        :newt_sessionid: (string) Session token from NEWT web service at NERSC.
           (Girder must be connected to NEWT service to authenicate.)
        """
        if self.__class__.is_initialized():
            msg = """GirderInterface already initialized -- \
                cannot initialize twice"""
            raise GaiaException(msg)

        self.girder_url = girder_url
        # Check that we have credentials

        api_url = '{}/api/v1'.format(girder_url)
        # print('api_url: {}'.format(api_url))
        self.gc = girder_client.GirderClient(apiUrl=api_url)

        if username is not None and password is not None:
            self.gc.authenticate(username=username, password=password)
        elif apikey is not None:
            self.gc.authenticate(apiKey=apikey)
        elif newt_sessionid is not None:
            self.nersc_requests = requests.Session()
            url = '{}/newt/authenticate/{}'.format(api_url, newt_sessionid)
            r = self.nersc_requests.put(url)
            r.raise_for_status()
            self.nersc_requests.cookies.update(dict(
                newt_sessionid=newt_sessionid))
            # self.nersc_requests.cookies.set('newt_sessionid', newt_sessionid)

            # Get scratch directory
            data = {
                'executable': '/usr/bin/echo $SCRATCH',
                'loginenv': 'true'
            }
            machine = 'cori'
            NERSC_URL = 'https://newt.nersc.gov/newt'
            url = '%s/command/%s' % (NERSC_URL, machine)
            r = self.nersc_requests.post(url, data=data)
            r.raise_for_status()
            print(r.json())

            self.gc.token = self.nersc_requests.cookies['girderToken']
        else:
            raise MissingParameterError('No girder credentials provided.')

        # Get user info
        self.user = self.gc.getUser('me')

        # Get or intialize Private/gaia/default folder
        private_list = self.gc.listFolder(
            # self.user['_id'], parentFolderType='user', name='Private')
            # HACK FOR DEMO - use public folder until we set up
            # mechanism to send girder token to js client
            self.user['_id'], parentFolderType='user', name='Public')
        try:
            private_folder = next(private_list)
        except StopIteration:
            raise GaiaException('User/Private folder not found')

        gaia_list = self.gc.listFolder(
            private_folder['_id'], parentFolderType='folder', name='gaia')
        try:
            self.gaia_folder = next(gaia_list)
        except StopIteration:
            description = 'Created by Gaia'
            self.gaia_folder = self.gc.createFolder(
                private_folder['_id'], 'gaia', description=description)

        default_list = self.gc.listFolder(
            self.gaia_folder['_id'], parentFolderType='folder', name='default')
        try:
            self.default_folder = next(default_list)
        except StopIteration:
            description = 'Created by Gaia'
            self.default_folder = self.gc.createFolder(
                self.gaia_folder['_id'], 'default', description=description)
            print('Created gaia/default folder')

    def lookup_url(self, path=None, job_id=None, test=False):
        """Returns internal url for resource at specified path

        :param path: (string) Girder path, from user's root to resource
        :param job_id: (string) Girder job id, represents processing job
            submitted to remote machine
        :param test: (boolean) if True, raise exception if resource not found

        Either path or job_id must be specified (but not both!)
        """
        if path:
            resource = self.lookup_resource(path, test)
            if resource is None:
                return None

            # (else) construct "gaia" url
            resource_type = resource['_modelType']
            resource_id = resource['_id']
            gaia_url = 'girder://{}/{}'.format(resource_type, resource_id)
            return gaia_url
        elif job_id:
            job_endpoint = 'jobs/{}'.format(job_id)
            job_info = self.gc.get(job_endpoint)
            if not job_info:
                raise GaiaException('Job not found on girder')

            status = job_info.get('status')
            if status != 'complete':
                print('job_info:\n', job_info)
                raise GaiaException(
                    'Job status not complete ({})'.format(status))

            output_folder_id = job_info.get('output', [])[0].get('folderId')
            # print('output_folder_id', output_folder_id)

            # Output filename is stored in metadata
            default_filename = 'output.tif'
            metadata = job_info.get('metadata', {})
            output_filename = metadata.get('outputFilename', default_filename)

            # Get item id
            params = dict(
                folderId=output_folder_id, name=output_filename, limit=1)
            output_list = self.gc.get('item', parameters=params)
            # print(output_list)
            if output_list:
                output_info = output_list[0]
                output_item_id = output_info.get('_id', 'missing')
                # print('Output file {} is item id {}'.format(
                #     output_filename, output_item_id))
            else:
                raise GaiaException(
                    'Output file {} not found'.format(output_filename))

            # Create gaia object for output
            gaia_url = 'girder://item/{}'.format(output_item_id)
            return gaia_url
        else:
            raise MissingParameterError(
                'Must specify either path or job_id argument')

    def lookup_resource(self, path, test=True):
        """Does lookup of resource at specified path

        :param path: (string) Girder path, from user's root to resource
        :param test: (boolean) if True, raise exception if resource not found
        :return: (object) resource info including _id, and name
        """
        if path.startswith('/'):
            girder_path = path
        else:
            girder_path = 'user/{}/{}'.format(self.user['login'], path)
        resource = self.gc.get(
            'resource/lookup', parameters={'path': girder_path, 'test': test})
        return resource

    def ls(self, path, text=None, name=None, offset=0, limit=40,
            formatted=True):
        """Returns list of files at specified girder path (folder)

        :param formatted: (bool) if true, return abridged, formatted list

        """
        # Lookup folder id for given path
        folder_resource = self.lookup_resource(path)
        folder_id = folder_resource.get('_id')

        # Get items in that folder
        gen = self.gc.listItem(folder_id)
        contents = list(gen)
        if not formatted:
            return contents

        # (else) generate a list of abridged, formatted items
        def sizeof_fmt(num, suffix='B'):
            '''Converts number to human-readable form'''
            for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
                if abs(num) < 1024.0:
                    return "%3.1f %s%s" % (num, unit, suffix)
                num /= 1024.0
            return "%.1f %s%s" % (num, 'Y', suffix)

        content_list = [None] * len(contents)
        for i, item in enumerate(contents):
            sizeof = sizeof_fmt(item.get('size'))
            content_list[i] = [sizeof, item.get('name')]

        return content_list

    @classmethod
    def _get_default_folder_id(cls):
        """Returns id for default folder

        For internal use only
        """
        instance = cls.get_instance()
        if instance.default_folder is None:
            return None
        # (else)
        return instance.default_folder.get('_id')

    @classmethod
    def _get_girder_client(cls):
        """Returns GirderClient instance

        For internal use only
        """
        if cls.instance is None:
            raise GaiaException('GirderInterface not initialized')

        if cls.instance.gc is None:
            raise GaiaException('GirderClient not initialized')

        return cls.instance.gc
