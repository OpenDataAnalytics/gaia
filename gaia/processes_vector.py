import logging
import numpy as np
import pandas as pd

from gaia.gdal_functions import gdal_zonalstats

try:
    import osr
except ImportError:
    from osgeo import osr
from geopandas import GeoDataFrame
import gaia.formats as formats
from gaia.core import GaiaException
from gaia.inputs import VectorFileIO, reproject
from gaia.processes_base import GaiaProcess

logger = logging.getLogger('gaia.processes')


class BufferProcess(GaiaProcess):
    """
    Generates a buffer polygon around the geometries of the input data.
    The size of the buffer is determined by the 'buffer_size' args key
    and the unit of measure should be meters.  If inputs are not in a
    metric projection they will be reprojected to EPSG:3857.
    """
    required_inputs = (('input', formats.VECTOR),)
    required_args = ('buffer_size',)
    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(BufferProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        original_projection = self.inputs[0].get_epsg()
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(int(original_projection))
        if not srs.GetAttrValue('UNIT').lower().startswith('met'):
            reproject(self.inputs[0], 3857)
        else:
            original_projection = None

        super(BufferProcess, self).compute()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        first_df = self.inputs[0].read()
        buffer = first_df.buffer(self.args['buffer_size'])
        buffer_df = GeoDataFrame(geometry=buffer)
        self.output.data = buffer_df
        self.output.write()
        if original_projection:
            reproject(self.output, original_projection)
            self.output.write()


class WithinProcess(GaiaProcess):
    """
    Similar to SubsetProcess but for vectors: calculates the features within
    a vector dataset that are within (or whose centroids are within) the
    polygons of a second vector dataset.
    """

    required_inputs = (('first', formats.VECTOR), ('second', formats.VECTOR))
    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(WithinProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(WithinProcess, self).compute()
        # TODO: Don't assume GeoPandas Dataframe. Could be PostGIS,Girder,etc.
        if len(self.inputs) != 2:
            raise GaiaException('WithinProcess requires 2 inputs')
        first_df = self.inputs[0].read()
        second_df = self.inputs[1].read()
        first_within = first_df[first_df.geometry.within(
            second_df.geometry.unary_union)]
        self.output.data = first_within
        self.output.write()


class IntersectsProcess(GaiaProcess):
    """
    Calculates the features within the first vector dataset that touch
    the features of the second vector dataset.
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(IntersectsProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(IntersectsProcess, self).compute()
        first_df = self.inputs[0].read()
        second_df = self.inputs[1].read()
        first_intersects = first_df[first_df.geometry.intersects(
            second_df.geometry.unary_union)]
        self.output.data = first_intersects
        self.output.write()
        logger.debug(self.output)


class DifferenceProcess(GaiaProcess):
    """
    Calculates which features of the first vector dataset do not
    intersect the features of the second dataset.
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(DifferenceProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(DifferenceProcess, self).compute()
        first_df = self.inputs[0].read()
        second_df = self.inputs[1].read()

        first_difference = first_df[-first_df.geometry.intersects(
            second_df.geometry.unary_union)]

        self.output.data = first_difference
        self.output.write()
        logger.debug(self.output)


class UnionProcess(GaiaProcess):
    """
    Combines two vector datasets into one.
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(UnionProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(UnionProcess, self).compute()
        first_df = self.inputs[0].read()
        second_df = self.inputs[1].read()

        uniondf = GeoDataFrame(pd.concat([first_df, second_df]))

        self.output.data = uniondf
        self.output.write()
        logger.debug(self.output)


class CentroidProcess(GaiaProcess):
    """
    Calculates the centroid point of a vector dataset.
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(CentroidProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(CentroidProcess, self).compute()
        first_df = self.inputs[0].read()

        first_centroids = first_df.geometry.centroid

        centroids = GeoDataFrame(first_centroids[first_df.centroid.within(
            first_df.geometry)])

        centroids.columns = ['geometry']
        self.output.data = centroids
        self.output.write()
        logger.debug(self.output)


class DistanceProcess(GaiaProcess):
    """
    Calculates the minimum distance from each feature of the first dataset
    to the nearest feature of the second dataset.
    """

    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(DistanceProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        property_name = 'min_dist'
        super(DistanceProcess, self).compute()
        first_df = self.inputs[0].read()
        second_df = self.inputs[1].read()

        first_gs = first_df.geometry

        second_gs = second_df.geometry

        first_length = len(first_gs)

        min_dist = np.empty(first_length)

        for i, first_features in enumerate(first_gs):
            min_dist[i] = np.min([first_features.distance(second_features)
                                  for second_features in second_gs])

        first_df[property_name] = min_dist

        self.output.data = first_df
        self.output.write()
        logger.debug(self.output)


class ZonalStatsProcess(GaiaProcess):
    """
    Calculates statistical values from a raster dataset for each polygon
    in a vector dataset.
    """
    required_inputs = (('zones', formats.VECTOR), ('raster', formats.RASTER))
    default_output = formats.VECTOR

    def __init__(self, **kwargs):
        super(ZonalStatsProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = VectorFileIO(name='result',
                                       uri=self.get_outpath())

    def compute(self):
        super(ZonalStatsProcess, self).compute()
        self.output.create_output_dir(self.output.uri)
        features = gdal_zonalstats(
            self.inputs[0].read(format=formats.JSON), self.inputs[1].read())
        self.output.data = GeoDataFrame.from_features(features)
        self.output.write()
