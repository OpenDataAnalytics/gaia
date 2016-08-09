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
import gdal, ogr, os
import numpy as np
import itertools

try:
    import osr
except ImportError:
    from osgeo import osr
from gaia.gaia_process import GaiaProcess
from gaia.geo.gdal_functions import gdal_calc, gdal_clip
from gaia.geo.geo_inputs import RasterFileIO
from skimage.graph import route_through_array
from math import sqrt,ceil



logger = logging.getLogger('gaia.geo')


class SubsetProcess(GaiaProcess):
    """
    Generates a raster dataset representing the portion of the input raster
    dataset that is contained within a vector polygon.
    """
    required_inputs = (('raster', formats.RASTER), ('clip', formats.JSON))
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
        self.validate()

    def compute(self):
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
    required_inputs = (('A', formats.RASTER),)
    required_args = ('calc',)
    default_output = formats.RASTER

    bands = None
    nodata = None
    all_bands = None
    output_type = None

    def __init__(self, calc=None, **kwargs):
        super(RasterMathProcess, self).__init__(**kwargs)
        self.calc = calc
        if not self.output:
            self.output = RasterFileIO(name='result', uri=self.get_outpath())
        self.validate()

    def compute(self):
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
                                     output_type=otype)

class leastCostPathProcess(GaiaProcess):
    """
    Least cost path analysis.
    """
    required_args = ()
    default_output = formats.JSON

    def __init__(self, **kwargs):
        super(leastCostPathProcess, self).__init__(**kwargs)
        if not self.output:
            self.output = RasterFileIO(name='result', uri=self.get_outpath())
        self.validate()

        if self.inputs:
            self.start_point = self.inputs[0]
            self.end_point = self.inputs[1]
            self.raster_layer = self.inputs[2]['raster']


    def pixelOffset2coord(self, rasterfn,xOffset,yOffset):
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        originX = geotransform[0]
        originY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        coordX = originX+pixelWidth*xOffset
        coordY = originY+pixelHeight*yOffset
        return coordX, coordY

    def array2shp(self, array, outSHPfn, rasterfn, pixelValue):

        # max distance between points
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        pixelWidth = geotransform[1]
        maxDistance = ceil(sqrt(2*pixelWidth*pixelWidth))
        print maxDistance

        # array2dict
        count = 0
        roadList = np.where(array == pixelValue)
        multipoint = ogr.Geometry(ogr.wkbMultiLineString)
        pointDict = {}
        for indexY in roadList[0]:
            indexX = roadList[1][count]
            Xcoord, Ycoord = self.pixelOffset2coord(rasterfn, indexX, indexY)
            pointDict[count] = (Xcoord, Ycoord)
            count += 1

        # dict2wkbMultiLineString
        multiline = ogr.Geometry(ogr.wkbMultiLineString)
        for i in itertools.combinations(pointDict.values(), 2):
            point1 = ogr.Geometry(ogr.wkbPoint)
            point1.AddPoint(i[0][0], i[0][1])
            point2 = ogr.Geometry(ogr.wkbPoint)
            point2.AddPoint(i[1][0], i[1][1])

            distance = point1.Distance(point2)

            # calculate the distance between two points
            if distance < maxDistance:
                line = ogr.Geometry(ogr.wkbLineString)
                line.AddPoint(i[0][0], i[0][1])
                line.AddPoint(i[1][0], i[1][1])
                multiline.AddGeometry(line)

        # wkbMultiLineString2shp
        shpDriver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(outSHPfn):
            shpDriver.DeleteDataSource(outSHPfn)
        outDataSource = shpDriver.CreateDataSource(outSHPfn)
        outLayer = outDataSource.CreateLayer(outSHPfn, geom_type=ogr.wkbMultiLineString )
        featureDefn = outLayer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(multiline)
        outLayer.CreateFeature(outFeature)


    def raster_to_array(self, raster):
        raster = gdal.Open(raster)
        band = raster.GetRasterBand(1)
        array = band.ReadAsArray()
        return array

    def coord2pixelOffset(self, rasterfn, x, y):
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        originX = geotransform[0]
        originY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        xOffset = int((x - originX)/pixelWidth)
        yOffset = int((y - originY)/pixelHeight)
        return xOffset, yOffset

    def createPath(self, raster, costSurfaceArray, start, end):

        # coordinates to array index
        startCoordX = start[0]
        startCoordY = start[1]
        startIndexX, startIndexY = self.coord2pixelOffset(raster, startCoordX, startCoordY)

        stopCoordX = end[0]
        stopCoordY = end[1]
        stopIndexX, stopIndexY = self.coord2pixelOffset(raster, stopCoordX, stopCoordY)

        # create path
        indices, weight = route_through_array(costSurfaceArray, (startIndexY, startIndexX), (stopIndexY, stopIndexX), geometric=True, fully_connected=True)
        indices = np.array(indices).T
        path = np.zeros_like(costSurfaceArray)
        path[indices[0], indices[1]] = 1
        return path

    def array_to_raster(self, newRasterfn, rasterfn, array):
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        originX = geotransform[0]
        originY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        cols = array.shape[1]
        rows = array.shape[0]

        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create(newRasterfn, cols, rows, gdal.GDT_Byte)
        outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
        outband = outRaster.GetRasterBand(1)
        outband.WriteArray(array)
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
        outRaster.SetProjection(outRasterSRS.ExportToWkt())
        outband.FlushCache()

    def calculatePath(self, raster, start, end):
        costSurfaceArray = self.raster_to_array(raster)
        pathArray = self.createPath(raster, costSurfaceArray, start, end)
        self.array2shp(pathArray, '../tests/data/output/least_cost.shp', raster,  1)

    def compute(self):
        data = self.calculatePath(self.raster_layer, self.start_point['start'], self.end_point['end'])
        self.output.data = data
        self.output.write()
        logger.debug(self.output)

