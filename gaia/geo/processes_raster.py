#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright Kitware Inc. and Epidemico Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
import logging
import gaia.formats as formats
from gaia.gaia_process import GaiaProcess
from gaia.geo.gdal_functions import gdal_calc, gdal_clip
from gaia.geo.geo_inputs import RasterFileIO
from gaia import types

logger = logging.getLogger('gaia.geo')


class SubsetProcess(GaiaProcess):
    """
    Generates a raster dataset representing the portion of the input raster
    dataset that is contained within a vector polygon.
    """
    #: Tuple of required inputs; name, type , max # of each; None = no max
    required_inputs = [
        {'description': 'Image to subset',
         'type': types.RASTER,
         'max': 1
         },
        {'description': 'Subset area:',
         'type': types.VECTOR,
         'max': 1
         }
    ]

    #: Default output format for the process
    default_output = formats.RASTER

    def __init__(self, **kwargs):
        """
        Create a process to subset a raster by a vector polygon

        :param clip_io: IO object containing vector polygon data
        :param raster_io: IO object containing raster data
        :param kwargs:
        :return: SubsetProcess object
        """
        super(SubsetProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = RasterFileIO(name='result', uri=self.get_outpath())

    def compute(self):
        """
        Runs the subset computation, creating a raster dataset as output.
        """
        raster, clip = self.inputs[0], self.inputs[1]
        raster_img = raster.read()
        clip_df = clip.read(epsg=raster.get_epsg())
        # Merge all features in vector input
        raster_output = self.output.uri
        self.output.create_output_dir(raster_output)
        clip_json = clip_df.geometry.unary_union.__geo_interface__
        self.output.data = gdal_clip(raster_img, raster_output, clip_json)


class RasterMathProcess(GaiaProcess):
    """
    Performs raster math/algebra based on supplied arguments.
    Inputs should consist of at least one raster IO object.
    Required arg is 'calc', an equation for the input rasters.
    Example: "A + B / (C * 2.4)".  The letters in the equation
    should correspond to the names of the inputs.
    """
    #: Tuple of required inputs; name, type , max # of each; None = no max
    required_inputs = [
        {'description': 'Image',
         'type': types.RASTER,
         'max': None
         }
    ]
    #: Required arguments for the process
    required_args = [{
        'name': 'calc',
        'title': 'Calculation',
        'description': 'Equation to apply to rasters (ex: "(A+B)/2"',
        'type': str
    }]
    #: Default output format for the process
    default_output = formats.RASTER

    #: Default input raster bands to process
    bands = None
    #: Default NODATA value for raster input
    nodata = None
    #: Use all bands in raster input (default: False)
    all_bands = False
    #: Default data type for raster (UInt32, Float, etc)
    output_type = None
    #: Image output format (default='GTiff')
    output_format = 'GTiff'

    def __init__(self, calc=None, **kwargs):
        """
        Initialize a RasterMathProcess object.

        :param calc: A text representation of the calculation to make.
        :param kwargs: Other keyword arguments
        """
        self.calc = calc
        super(RasterMathProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = RasterFileIO(name='result', uri=self.get_outpath())

    def compute(self):
        """
        Run the RasterMath process, generating a raster output dataset.
        """
        first = self.inputs[0]
        epsg = first.get_epsg()
        rasters = [x.read(epsg=epsg) for x in self.inputs]
        bands = self.bands
        nodata = self.nodata
        all_bands = self.all_bands
        otype = self.output_type
        self.output.create_output_dir(self.output.uri)
        self.output.data = gdal_calc(self.calc,
                                     self.output.uri,
                                     rasters,
                                     bands=bands,
                                     nodata=nodata,
                                     allBands=all_bands,
                                     output_type=otype,
                                     format=self.output_format)


class ClusterProcess(GaiaProcess):
    """
    Cluster raster dataset to produce cluster assignment raster.
    """
    #: Tuple of required inputs; name, type , max # of each; None = no max
    required_inputs = [
        {'description': 'Raster to cluster',
         'type': types.RASTER,
         'max': 1
         }
    ]
    #: Required arguments for the process
    required_args = [{
        'name': 'method',
        'title': 'Method',
        'description': 'Clustering algorithm to use.',
        'type': str
    }]

    #: Default output format for the process
    default_output = formats.RASTER

    def __init__(self, **kwargs):
        """
        Create a process for raster cell clustering.

        :param inputs: Raster to run clustering on.
        :param method: Clustering algorithm to use.
        :param kwargs: Other keyword arguments.
        :return: ClusterProcess object.
        """
        super(ClusterProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = RasterFileIO(name='result', uri=self.get_outpath())

    def compute(self):
        """
        Runs the cell clustering, creating a raster cluster assignment dataset as output.
        """

        # Read data.
        input_image = self.inputs[0].read()

        # Cluster assignments.
        #self.output.data = output_image
