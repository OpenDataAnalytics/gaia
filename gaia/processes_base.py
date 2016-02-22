import os
import uuid
from gaia.core import get_abspath, config
from gaia.inputs import reproject


class GaiaProcess(object):
    """
    Defines a process to run on geospatial inputs
    """

    # TODO: Enforce required inputs and args
    required_inputs = tuple()
    required_args = tuple()

    def __init__(self, inputs=None, output=None, args=None, parent=None):
        self.inputs = inputs
        self.output = output
        self.args = args
        self.parent = parent
        self.id = str(uuid.uuid4())

    def compute(self):
        previous_input = None
        for input in self.inputs:
            if input.data is None:
                input.read()
            if previous_input:
                if input.get_epsg() != previous_input.get_epsg():
                    reproject(input, previous_input.epsg)
            previous_input = input

    def purge(self):
        self.output.delete()

    def get_outpath(self, uri=config['gaia']['output_path']):
        ids_path = '{}/{}'.format(
            self.parent, self.id) if self.parent else self.id
        return get_abspath(
            os.path.join(uri, ids_path,
                         '{}{}'.format(self.id, self.default_output[0])))
