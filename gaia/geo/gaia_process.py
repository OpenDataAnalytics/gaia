import os
import uuid
from gaia.core import get_abspath, config, GaiaException


class GaiaProcess(object):
    """
    Defines a process to run on geospatial inputs
    """

    # TODO: Enforce required inputs and args
    required_inputs = tuple()
    required_args = tuple()

    args = None

    def __init__(self, inputs=None, output=None, parent=None, **kwargs):
        self.inputs = inputs
        self.output = output
        self.parent = parent
        self.id = str(uuid.uuid4())
        for k, v in kwargs.items():
            setattr(self, k, v)

    def validate(self):
        if len(self.inputs) < len(self.required_inputs):
            raise GaiaException("Process requires a minimum of {} inputs".
                                format(len(self.required_inputs)))
        for arg in self.required_args:
            if not hasattr(self, arg) or getattr(self, arg) is None:
                raise GaiaException('Missing required argument {}'.format(arg))

    def compute(self):
        raise NotImplementedError()

    def purge(self):
        self.output.delete()

    def get_outpath(self, uri=config['gaia']['output_path']):
        ids_path = '{}/{}'.format(
            self.parent, self.id) if self.parent else self.id
        return get_abspath(
            os.path.join(uri, ids_path,
                         '{}{}'.format(self.id, self.default_output[0])))

    def get_input_classes(self):
        """
        Return a unique set of input classes
        :return:
        """
        io_classes = set()
        for input in self.inputs:
            input_class = input.__class__.__name__
            if 'Process' not in input_class:
                io_classes.add(input.__class__.__name__)
            else:
                io_classes = io_classes.union(input.process.get_input_classes())
        return io_classes
