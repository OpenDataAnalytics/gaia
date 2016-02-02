import importlib
import traceback
import gaia.core
import gaia.inputs
from gaia.inputs import formats
import logging
from geopandas import GeoDataFrame


__author__ = 'mbertrand'

gaia_process_class_dict = {
    'reproject': 'ReprojectProcess',
    'subset': 'SubsetProcess',
    'buffer': 'BufferProcess'
}

logger = logging.getLogger('gaia')


class GaiaProcess(object):
    """
    Defines a process to run on geospatial inputs
    """

    required_args = tuple()
    output = None

    def __init__(self, inputs=None, args=None):
        self.inputs = inputs
        self.args = args

    def calculate(self):
        for input in self.inputs:
            if not input.io.data:
                input.io.read()


class BufferProcess(GaiaProcess):

    required_inputs = (('input', formats.VECTOR),)
    required_args = ('buffer_size',)

    def calculate(self):
        super(BufferProcess, self).calculate()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        first_df = self.inputs[0].data()
        buffer = first_df.buffer(self.args['buffer_size'])
        buffer_df = GeoDataFrame(geometry=buffer)
        self.raw_output = buffer_df
        self.output = gaia.inputs.GaiaOutput('result',
                                             self.raw_output.to_json())
        logger.debug(self.output)


class SubsetVectorProcess(GaiaProcess):

    required_inputs = (('input', formats.ALL),)
    required_args = ('subset_area',)

    def calculate(self):
        super(SubsetVectorProcess, self).calculate()
        self.output = {
            "Process": "Subset; real output will be GeoJSON FeatureCollection"
        }
        logger.debug(self.output)


class SubsetRasterProcess(GaiaProcess):

    required_inputs = (('input', formats.ALL),)
    required_args = ('subset_area',)

    def calculate(self):
        super(SubsetRasterProcess, self).calculate()
        self.output = {
            "Process": "Subset; real output will be GeoTIFF"
        }
        logger.debug(self.output)


class WithinProcess(GaiaProcess):

    required_inputs = (('first', formats.VECTOR), ('second', formats.VECTOR))

    def calculate(self):
        super(WithinProcess, self).calculate()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()
        first_within = first_df[first_df.geometry.within(
            second_df.geometry.unary_union)]
        self.raw_output = first_within
        self.output = gaia.inputs.GaiaOutput('result', self.raw_output.to_json())
        logger.debug(self.output)


def create_process(name):
    """
    Return an object of a particular Process class based on the input string.
    :param name:
    :return:
    """
    m = importlib.import_module('gaia.processes.base')
    try:
        class_name = '{}Process'.format(name.capitalize())
        return getattr(m, class_name)()
    except AttributeError as e:
        raise gaia.core.GaiaException(traceback.format_exc())
