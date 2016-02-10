import importlib
import traceback
import logging
from geopandas import GeoDataFrame
from gaia.core import get_abspath
from gaia.inputs import *
from gaia.gdal_functions import gdal_clip

logger = logging.getLogger('gaia')


class GaiaProcess(object):
    """
    Defines a process to run on geospatial inputs
    """

    required_args = tuple()

    def __init__(self, inputs=None, output=None, args=None, parent=None):
        self.inputs = inputs
        self.output = output
        self.args = args
        self.parent = parent
        self.id = str(uuid.uuid4())

    def compute(self):
        for input in self.inputs:
            if input.data is None:
                input.read()

    def purge(self):
        self.output.delete()

    def get_outpath(self, uri=config['gaia']['output_path']):
        ids_path = '{}/{}'.format(
            self.id, self.parent) if self.parent else self.id
        return get_abspath(os.path.join(uri, ids_path,
                         '{}{}'.format(self.id, self.default_output[0])))


class BufferProcess(GaiaProcess):

    required_inputs = (('input', formats.VECTOR),)
    required_args = ('buffer_size',)
    default_output = formats.JSON

    def __init__(self, inputs=None, output=None, args=None, parent=None):
        super(BufferProcess, self).__init__(inputs, output, args)
        if not output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(BufferProcess, self).compute()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        first_df = self.inputs[0].data
        buffer = first_df.buffer(self.args['buffer_size'])
        buffer_df = GeoDataFrame(geometry=buffer)
        self.output.data = buffer_df
        self.output.write()
        logger.debug(self.output)


class SubsetVectorProcess(GaiaProcess):

    required_inputs = (('input', formats.ALL),)
    required_args = ('subset_area',)
    default_output = formats.JSON

    def __init__(self, inputs=None, output=None, args=None, parent=None):
        super(SubsetVectorProcess, self).__init__(inputs, output, args)
        if not output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(SubsetVectorProcess, self).compute()
        self.output = {
            "Process": "Subset; real output will be GeoJSON FeatureCollection"
        }
        logger.debug(self.output)


class SubsetRasterProcess(GaiaProcess):

    required_inputs = (('clip', formats.JSON), ('raster', formats.RASTER))
    default_output = formats.RASTER

    def __init__(self, inputs=None, output=None, args=None, parent=None):
        super(SubsetRasterProcess, self).__init__(inputs, output, args)
        if not output:
            self.output = RasterFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(SubsetRasterProcess, self).compute()
        clip_df = None
        raster_img = None
        for input in self.inputs:
            if input.name == 'clip':
                clip_df = input.read()
            elif input.name == 'raster':
                raster_img = input.read()
        # Merge all features in vector input
        raster_output = self.output.uri
        print raster_output
        self.output.create_output_dir(raster_output)
        clip_json = clip_df.geometry.unary_union.__geo_interface__
        self.output.data = gdal_clip(raster_img, raster_output, clip_json)


class WithinProcess(GaiaProcess):

    def __init__(self, inputs=None, output=None, args=None, parent=None):
        super(WithinProcess, self).__init__(inputs, output, args)
        if not output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(WithinProcess, self).compute()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.read()
            elif input.name == 'second':
                second_df = input.read()
        first_within = first_df[first_df.geometry.within(
            second_df.geometry.unary_union)]
        self.output.data = first_within
        self.output.write()

    required_inputs = (('first', formats.VECTOR), ('second', formats.VECTOR))
    default_output = formats.JSON


def create_process(name, parent=None):
    """
    Return an object of a particular Process class based on the input string.
    :param name:
    :return:
    """
    m = importlib.import_module('gaia.processes')
    try:
        class_name = '{}Process'.format(name[0].capitalize() + name[1:])
        return getattr(m, class_name)({parent: parent})
    except AttributeError:
        raise GaiaException(traceback.format_exc())

