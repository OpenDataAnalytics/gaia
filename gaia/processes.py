import logging
import uuid
import os
from geopandas import GeoDataFrame
from gaia.core import get_abspath, config
from gaia.inputs import VectorFileIO, RasterFileIO
import gaia.formats as formats
from gaia.gdal_functions import gdal_clip
import numpy as np
import pandas as pd

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
            self.parent, self.id) if self.parent else self.id
        return get_abspath(
            os.path.join(uri, ids_path,
                         '{}{}'.format(self.id, self.default_output[0])))


class BufferProcess(GaiaProcess):
    """
       --------- BUFFER PROCESS ------------
    """
    required_inputs = (('input', formats.VECTOR),)
    required_args = ('buffer_size',)
    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(BufferProcess, self).__init__(**kwargs)
        if not self.output:
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
    """
       --------- SUBSET VECTOR PROCESS ------------
    """
    required_inputs = (('input', formats.ALL),)
    required_args = ('subset_area',)
    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(SubsetVectorProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(SubsetVectorProcess, self).compute()
        self.output = {
            "Process": "Subset; real output will be GeoJSON FeatureCollection"
        }
        logger.debug(self.output)


class SubsetRasterProcess(GaiaProcess):
    """
       --------- SUBSET RASTER PROCESS ------------
    """
    required_inputs = (('clip', formats.JSON), ('raster', formats.RASTER))
    default_output = formats.RASTER

    def __init__(self, **kwargs):
        super(SubsetRasterProcess, self).__init__(**kwargs)
        if not self.output:
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
        self.output.create_output_dir(raster_output)
        clip_json = clip_df.geometry.unary_union.__geo_interface__
        self.output.data = gdal_clip(raster_img, raster_output, clip_json)


class WithinProcess(GaiaProcess):
    """
       --------- WITHIN PROCESS ------------
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(WithinProcess, self).__init__(**kwargs)
        if not self.output:
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


class IntersectsProcess(GaiaProcess):
    """
       --------- INTERSECTS PROCESS ------------
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(IntersectsProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(IntersectsProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.read()
            elif input.name == 'second':
                second_df = input.read()
        first_intersects = first_df[first_df.geometry.intersects(
            second_df.geometry.unary_union)]
        self.output.data = first_intersects
        self.output.write()
        logger.debug(self.output)


class DifferenceProcess(GaiaProcess):
    """
       --------- DIFFERENCE PROCESS ------------
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(DifferenceProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(DifferenceProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.read()
            elif input.name == 'second':
                second_df = input.read()

        first_difference = first_df[first_df.geometry.intersects(
            second_df.geometry.unary_union) == False]

        self.output.data = first_difference
        self.output.write()
        logger.debug(self.output)


class UnionProcess(GaiaProcess):
    """
       --------- UNION PROCESS ------------
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(UnionProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(UnionProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.read()
            elif input.name == 'second':
                second_df = input.read()

        uniondf = GeoDataFrame(pd.concat([first_df, second_df]))

        self.output.data = uniondf
        self.output.write()
        logger.debug(self.output)


class CentroidProcess(GaiaProcess):
    """
       --------- CENTROID PROCESS ------------
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(CentroidProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        super(CentroidProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.read()

        first_centroids = first_df.geometry.centroid

        centroids = GeoDataFrame(first_centroids[first_df.centroid.within(
            first_df.geometry)])

        centroids.columns = ['geometry']
        self.output.data = centroids
        self.output.write()
        logger.debug(self.output)


class DistanceProcess(GaiaProcess):
    """
       --------- DISTANCE PROCESS ------------
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(DistanceProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO('result',
                                       uri=self.get_outpath())

    def compute(self):
        PROPERTY_NAME = 'min_dist'
        super(DistanceProcess, self).compute()
        for input in self.inputs:
            if input.name == 'first':
                first_df = input.read()
            elif input.name == 'second':
                second_df = input.read()

        first_gs = first_df.geometry

        second_gs = second_df.geometry

        first_length = len(first_gs)

        min_dist = np.empty(first_length)

        for i, first_features in enumerate(first_gs):
            min_dist[i] = np.min([first_features.distance(second_features)
                                  for second_features in second_gs])

        first_df[PROPERTY_NAME] = min_dist

        self.output.data = first_df
        self.output.write()
        logger.debug(self.output)
