import importlib
import os
import traceback
import uuid
import errno
import logging
from geopandas import GeoDataFrame, GeoSeries
import gaia.core
import gaia.inputs
from gaia.inputs import formats
import logging
from geopandas import GeoDataFrame
import pandas as pd
import numpy as np
from gaia.processes.gdal_functions import gdal_clip


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
        self.id = str(uuid.uuid4())
        config = gaia.core.getConfig()
        self.outpath = config['gaia']['output_path']

    def compute(self):
        for input in self.inputs:
            if not input.io.data:
                input.io.read()


"""
   --------- BUFFER PROCESS ------------
"""

class BufferProcess(GaiaProcess):

    required_inputs = (('input', formats.VECTOR),)
    required_args = ('buffer_size',)
    default_output = formats.JSON

    def compute(self):
        super(BufferProcess, self).compute()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        first_df = self.inputs[0].data()
        buffer = first_df.buffer(self.args['buffer_size'])
        buffer_df = GeoDataFrame(geometry=buffer)
        self.raw_output = buffer_df
        self.output = gaia.inputs.GaiaOutput('result',
                                             self.raw_output.to_json())
        logger.debug(self.output)


"""
   --------- SUBSET VECTOR PROCESS ------------
"""

class SubsetVectorProcess(GaiaProcess):

    required_inputs = (('input', formats.ALL),)
    required_args = ('subset_area',)
    default_output = formats.JSON

    def compute(self):
        super(SubsetVectorProcess, self).compute()
        self.output = {
            "Process": "Subset; real output will be GeoJSON FeatureCollection"
        }
        logger.debug(self.output)


"""
   --------- SUBSET RASTER PROCESS ------------
"""

class SubsetRasterProcess(GaiaProcess):

    required_inputs = (('clip', formats.JSON), ('raster', formats.RASTER))
    default_output = formats.RASTER

    def compute(self):
        super(SubsetRasterProcess, self).compute()
        clip_df = None
        raster_img = None
        for input in self.inputs:
            if input.name == 'clip':
                clip_df = input.data()
            elif input.name == 'raster':
                raster_img = input.data()
        # Merge all features in vector input
        output_name = '{}.tif'.format(self.id)
        raster_output = os.path.abspath(
            os.path.join(self.outpath, self.id, output_name))
        create_output_dir(raster_output)
        clip_json = clip_df.geometry.unary_union.__geo_interface__
        self.raw_output = gdal_clip(raster_img, raster_output, clip_json)
        self.output = gaia.inputs.GaiaOutput('result', self.raw_output,
                                             file=raster_output)




"""
   --------- WITHIN PROCESS ------------
"""

class WithinProcess(GaiaProcess):
    def compute(self):
        super(WithinProcess, self).compute()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()
        first_within = first_df[first_df.geometry.within(
            second_df.geometry.unary_union)]
        self.raw_output = first_within
        self.output = gaia.inputs.GaiaOutput('result',
                                             self.raw_output.to_json())
        logger.debug(self.output)

    required_inputs = (('first', formats.VECTOR), ('second', formats.VECTOR))
    default_output = formats.JSON


def create_output_dir(filename):
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise





"""
   --------- INTERSECTS PROCESS ------------
"""

class IntersectsProcess(GaiaProcess):

    def compute(self):
        super(IntersectsProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()
        first_intersects = first_df[first_df.geometry.intersects(
            second_df.geometry.unary_union)]
        self.raw_output = first_intersects
        self.output = gaia.inputs.GaiaOutput('result', self.raw_output.to_json())
        logger.debug(self.output)


"""
   --------- DIFFERENCE PROCESS ------------
"""

class DifferenceProcess(GaiaProcess):

    def compute(self):
        super(DifferenceProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()

        first_intersects = first_df[first_df.geometry.intersects(
            second_df.geometry.unary_union) == False]
        
        self.raw_output = first_intersects
        self.output = gaia.inputs.GaiaOutput('result', self.raw_output.to_json())
        logger.debug(self.output)


"""
   --------- UNION PROCESS ------------
"""

class UnionProcess(GaiaProcess):

    def compute(self):
        super(UnionProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()

        uniondf = GeoDataFrame(pd.concat([first_df, second_df]))

        self.raw_output = uniondf
        self.output = gaia.inputs.GaiaOutput('result', self.raw_output.to_json())
        logger.debug(self.output)


"""
   --------- CENTROID PROCESS ------------
"""

class CentroidProcess(GaiaProcess):

    def compute(self):
        super(CentroidProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()

        first_centroids = first_df.geometry.centroid

        centroids = GeoDataFrame(first_centroids[first_df.centroid.within(
            first_df.geometry)])

        centroids.columns = ['geometry']

        self.raw_output = centroids
        self.output = gaia.inputs.GaiaOutput('result', self.raw_output.to_json())
        logger.debug(self.output)

"""
   --------- DISTANCE PROCESS ------------
"""

class DistanceProcess(GaiaProcess):

    def compute(self):
        PROPERTY_NAME = 'min_dist'
        super(DistanceProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.data()
            elif input.name == 'second':
                second_df = input.data()

        first_gs = first_df.geometry

        second_gs = second_df.geometry

        first_length = len(first_gs)

        min_dist = np.empty(first_length)

        for i, first_features in enumerate(first_gs):
            min_dist[i] = np.min([first_features.distance(second_features) for second_features in second_gs])

        first_df[PROPERTY_NAME] = min_dist

        self.raw_output = first_df
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
        class_name = '{}Process'.format(name[0].capitalize() + name[1:])
        return getattr(m, class_name)()
    except AttributeError:
        raise gaia.core.GaiaException(traceback.format_exc())

