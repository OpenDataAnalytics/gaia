# =============================================================================
#
#  Copyright (c) Kitware, Inc.
#  All rights reserved.
#  See LICENSE.txt for details.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notice for more information.
#
# =============================================================================
import datetime
import io
import json
import os
import time
import uuid

from girder_client import HttpError
import requests

import gaia
from gaia.girder_data import GirderDataObject
from gaia.io.girder_interface import GirderInterface
from gaia.util import GaiaException

NERSC_URL = 'https://newt.nersc.gov/newt'

# Some hard-coded constants for now
MACHINE = 'cori'
JOHNT_PATH = '/global/homes/j/johnt'
CONDA_ENV_PATH = '{}/.conda/envs/py3'.format(JOHNT_PATH)
PROJECT_PATH = '{}/project'.format(JOHNT_PATH)
GAIA_PATH = '{}/git/gaia'.format(PROJECT_PATH)


class CumulusInterface():
    """An internal class that submits jobs to NERSC via girder/cumulus

    This class uses the girder client owned by GirderInterface, which must be
    authenticated with NERSC (NEWT api). Note that this version is hard-coded
    to the Cori machine.
    """

    # ---------------------------------------------------------------------
    def __init__(self):
        """Recommend using separate instance for each job submission.
        """
        self._girder_client = None
        self._nersc_scratch_folder = None
        self._private_folder_id = None

        # Internal, job-specific ids
        self._cluster_id = None
        self._input_folder_id = None
        self._job_folder_id = None
        self._job_id = None
        self._output_folder_id = None
        self._script_id = None

        girder_interface = GirderInterface.get_instance()
        if girder_interface.nersc_requests is None:
            msg = """GirderInterface is not configured for NERSC job submission -- \
must authenticate with NEWT session id."""
            raise GaiaException(msg)

        # Get user's scratch directory
        data = {
            'executable': 'echo $SCRATCH',
            'loginenv': 'true'
        }
        machine = 'cori'
        url = '%s/command/%s' % (NERSC_URL, machine)
        r = girder_interface.nersc_requests.post(url, data=data)
        r.raise_for_status()
        js = r.json()
        self._nersc_scratch_folder = js.get('output')

        # Get Girder client
        self._girder_client = girder_interface.gc

        # Get id for user's private girder folder
        user = self._girder_client.get('user/me')
        print('user', user)
        user_id = user['_id']
        # r = self._girder_client.listFolder(user_id, 'user', name='Private')
        r = self._girder_client.listFolder(user_id, 'user', name='Public')
        # Getting mixed signals on what listFolder returns
        # I *think* it is a generator
        try:
            self._private_folder_id = next(r)['_id']
        except Exception:
            # But just in case
            self._private_folder_id = r[0]['_id']
        # print('private_folder_id', self._private_folder_id)

    # ---------------------------------------------------------------------
    def submit_crop(
            self,
            input_object,
            crop_object,
            nersc_repository,
            job_name='geolib'):
        """
        """
        # Validate inputs
        if not isinstance(input_object, GirderDataObject):
            print('input object type', type(input_object))
            raise GaiaException("""submit_crop() currently only supports \
GirderDataObject input""")
        if not crop_object._getdatatype() == gaia.types.VECTOR:
            raise GaiaException('Crop object not type VECTOR')

        # Get input object's filename
        # For now (March 2019) we are storing a cache of files on cori
        # for the ESS-DIVE dev server
        item = self._girder_client.getItem(input_object.resource_id)
        input_filename = item.get('name')

        # Call internal methods in this order
        #   create_cluster()
        #   create_slurm_script()
        #   create_job()
        #   upload_inputs()
        #   submit_job()
        print('Creating cluster on {}'.format(MACHINE))
        self.create_cluster(MACHINE)

        # Create SLURM commands
        print('Creating SLURM script {}'.format(job_name))
        command_list = list()
        command_list.append('ulimit -s unlimited')  # stack size
        command_list.append('module load python/3.6-anaconda-4.4')
        command_list.append('source activate {}'.format(CONDA_ENV_PATH))
        command_list.append('export PYTHONPATH={}'.format(GAIA_PATH))

        # Last command is the python script itself
        py_script = '{}/nersc/crop.py'.format(GAIA_PATH)

        # For now, we have chache copies of input files on cori:
        input_path = '{}/data/{}'.format(PROJECT_PATH, input_filename)
        geometry_filename = 'crop_geometry.geojson'
        output_filename = 'output.tif'
        py_command = 'python {} {} {} {}'.format(
            py_script, input_path, geometry_filename, output_filename)

        # Arguments
        # -n number of nodes
        # -c number of cpus per allocated process
        # -u unbuffered (don't buffer terminal output - needed by cumulus)
        command_list.append('srun -n 1 -c 1 -u {}'.format(py_command))
        self.create_slurm_script('metadata', command_list)

        print('Creating job {}'.format(job_name))
        self.create_job(job_name)

        # Set job metadata - keywords used by smtk job panel
        job_metadata = dict()
        # job_metadata['solver'] = solver
        job_metadata['notes'] = ''
        number_of_nodes = 1
        job_metadata['numberOfNodes'] = number_of_nodes
        # Total number of cores (1 core per task times number of nodes)
        number_of_tasks = 1
        job_metadata['numberOfCores'] = number_of_nodes * number_of_tasks

        # Time stamp (seconds since epoci)
        job_metadata['startTimeStamp'] = time.time()

        # Plus one specific to our job
        job_metadata['outputFilename'] = output_filename
        self.set_job_metadata(job_metadata)

        print('Uploading geometry file')
        name = geometry_filename
        geom_string = crop_object.get_data().to_json()
        size = len(geom_string)
        # print('geom_string:', geom_string)
        geom_stream = io.StringIO(geom_string)
        self._girder_client.uploadFile(
            self._input_folder_id, geom_stream, name, size, parentType='folder')

        print('Submitting job')
        datecode = datetime.datetime.now().strftime('%y%m%d')
        output_dir = '{}/geolib/{}/{}'.format(
            self._nersc_scratch_folder, datecode, job_name)
        return self.submit_job(MACHINE, nersc_repository, output_dir)

    # ---------------------------------------------------------------------
    def create_cluster(self, machine_name, cluster_name=None):
        '''
        '''
        if cluster_name is None:
            user = self._girder_client.get('user/me')
            user_name = user.get('firstName', 'user')
            cluster_name = '%s.%s' % (machine_name, user_name)

        cluster = None
        cluster_list = self._girder_client.get('clusters')
        for extant_cluster in cluster_list:
            if extant_cluster['name'] == cluster_name:
                cluster = extant_cluster
                self._cluster_id = extant_cluster['_id']
                break

        if not cluster:
            body = {
                'config': {
                    'host': machine_name
                },
                'name': cluster_name,
                'type': 'newt'
            }

            r = self._girder_client.post('clusters', data=json.dumps(body))
            self._cluster_id = r['_id']
            print('cluster_id', self._cluster_id)

        # Reset the state of the cluster
        body = {
            'status': 'created'
        }
        endpoint = 'clusters/%s' % self._cluster_id
        r = self._girder_client.patch(endpoint, data=json.dumps(body))

        # Now test the connection
        r = self._girder_client.put('clusters/%s/start' % self._cluster_id)
        sleeps = 0
        while True:
            time.sleep(1)
            r = self._girder_client.get('clusters/%s/status' % self._cluster_id)
            # print('status', r['status'])

            if r['status'] == 'running':
                break
            elif r['status'] == 'error':
                r = self._girder_client.get(
                    'clusters/%s/log' % self._cluster_id)
                print(r)
                raise Exception('ERROR creating cluster')

            if sleeps > 9:
                raise Exception('Cluster never moved into running state')
            sleeps += 1

    # ---------------------------------------------------------------------
    def create_slurm_script(self, name, command_list):
        '''Creates script to submit job
        '''
        body = {
            'commands': command_list,
            'name': name
        }
        r = self._girder_client.post('scripts', data=json.dumps(body))
        self._script_id = r['_id']
        print('script_id', self._script_id)

    # ---------------------------------------------------------------------
    def create_job(self, job_name, tail=None):
        '''
        '''
        # Create job folders
        folder_name = uuid.uuid4().hex  # unique name
        self._job_folder_id = self.get_folder(
            self._private_folder_id, folder_name)
        print('Created job folder', folder_name)
        self._input_folder_id = self.get_folder(
            self._job_folder_id, 'input_files')
        self._output_folder_id = self.get_folder(
            self._job_folder_id, 'output_files')
        # Make sure job_name isn't null
        if not job_name:
            job_name = 'CumulusJob'

        # Create job spec
        body = {
            'name': job_name,
            'scriptId': self._script_id,
            'output': [{
                'folderId': self._output_folder_id,
                'path': '.'
            }],
            'input': [
                {
                    'folderId': self._input_folder_id,
                    'path': '.'
                }
            ]
        }

        if tail:
            body['output'].append({
                "path": tail,
                "tail": True
            })

        job = self._girder_client.post('jobs', data=json.dumps(body))
        self._job_id = job['_id']
        print('Created job_id', self._job_id)

    # ---------------------------------------------------------------------
    def upload_inputs(self, files_to_upload, folders_to_upload=[]):
        '''Uploads input files to (girder) input folder
        '''
        if not self._input_folder_id:
            raise Exception('Input folder missing')

        def upload_file(path):
            name = os.path.basename(path)
            size = os.path.getsize(path)
            with open(path, 'rb') as fp:
                self._girder_client.uploadFile(
                    self._input_folder_id, fp, name, size, parentType='folder')

        for file_path in files_to_upload:
            if not file_path or not os.path.exists(file_path):
                raise Exception('Input file not found: %s' % file_path)
            upload_file(file_path)

        for folder_path in folders_to_upload:
            if not folder_path or not os.path.exists(folder_path):
                raise Exception('Input folder not found: %s' % folder_path)
            # Create folder on girder
            basename = os.path.basename(folder_path)
            new_folder = self._girder_client.createFolder(
                self._input_folder_id, basename)
            # Upload files
            pattern = '%s/*' % folder_path
            self._girder_client.upload(pattern, new_folder._id)

    # ---------------------------------------------------------------------
    def submit_job(self,
                   machine,
                   project_account,
                   job_output_dir,
                   timeout_minutes=5,
                   queue='debug',
                   qos=None,
                   number_of_nodes=1):
        '''
        '''
        body = {
            'machine': machine,
            'account': project_account,
            'numberOfNodes': number_of_nodes,
            'maxWallTime': {
                'hours': 0,
                'minutes': timeout_minutes,
                'seconds': 0
            },
            'queue': queue,
        }
        if 'cori' == machine:
            body['constraint'] = 'knl'

        if qos:
            body['qualityOfService'] = qos

        body['jobOutputDir'] = job_output_dir

        print('submit_job body:', body)
        url = 'clusters/%s/job/%s/submit' % (self._cluster_id, self._job_id)
        self._girder_client.put(url, data=json.dumps(body))
        print('Submitted job', self._job_id)
        return self._job_id

    # ---------------------------------------------------------------------
    def set_job_metadata(self, meta):
        '''Writes metadata to job
        '''
        body = dict()
        body['metadata'] = meta
        self._girder_client.patch(
            'jobs/%s' % self._job_id, data=json.dumps(body))

    # ---------------------------------------------------------------------
    def download_results(self, destination_folder):
        '''Downloads all output files to a local directory

        '''
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        self._girder_client.downloadFolderRecursive(
            self._output_folder_id, destination_folder)

        print('Downloaded files to %s' % destination_folder)

    # ---------------------------------------------------------------------
    def release_resources(self):
        '''Closes/deletes any current resources

        '''
        resource_info = {
            'clusters': [self._cluster_id],
            'jobs': [self._job_id],
            'scripts': [self._script_id],
            'folder': [self._job_folder]
        }
        for resource_type, id_list in resource_info.items():
            for resource_id in id_list:
                if resource_id is not None:
                    url = '%s/%s' % (resource_type, resource_id)
                    self._girder_client.delete(url)

        self._input_folder_id = None
        self._job_folder_id = None
        self._job_id = None
        self._output_folder_id = None
        self._script_id = None

    # ---------------------------------------------------------------------
    def get_folder(self, parent_id, name):
        '''Returns folder_id, creating one if needed
        '''
        # Check if folder already exists
        folder_list = list(self._girder_client.listFolder(parent_id, name=name))
        if folder_list:
            folder = folder_list[0]
            return folder['_id']

        # (else)
        try:
            r = self._girder_client.createFolder(parent_id, name)
            return r['_id']
        except HttpError as e:
            print(e.responseText)

        return None
