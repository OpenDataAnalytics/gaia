import string
import os
import json
import logging
import gdalconst
import numpy
import gdal
import gdalnumeric
import ogr
import osr
from PIL import Image, ImageDraw
from osgeo.gdal_array import BandReadAsArray, BandWriteArray

logger = logging.getLogger('gaia.gdal_functions')


def gdal_reproject(src, dst,
                   epsg=3857,
                   error_threshold=0.125,
                   resampling=gdal.GRA_NearestNeighbour):
    """
    Reproject a raster image
    :param src: The source image
    :param dst: The filepath/name of the output image
    :param epsg: The EPSG code to reproject to
    :param error_threshold: Default is 0.125 (same as gdalwarp commandline)
    :param resampling: Default method is Nearest Neighbor
    """
    # Open source dataset
    src_ds = get_dataset(src)

    # Define target SRS
    dst_srs = osr.SpatialReference()
    dst_srs.ImportFromEPSG(int(epsg))
    dst_wkt = dst_srs.ExportToWkt()

    # Call AutoCreateWarpedVRT() to fetch default values
    # for target raster dimensions and geotransform
    reprojected_ds = gdal.AutoCreateWarpedVRT(src_ds,
                                              None,
                                              dst_wkt,
                                              resampling,
                                              error_threshold)

    # Create the final warped raster
    gdal.GetDriverByName('GTiff').CreateCopy(dst, reprojected_ds)
    return reprojected_ds


def gdal_resize(raster, dimensions, projection, transform):
    """
    Transform a dataset to the specified dimensions and projection/bounds
    :param dataset: Dataset to be resized
    :param dimensions: dimensions to resize to (X, Y)
    :param projection: Projection of of resized dataset
    :param transform: Geotransform of resized dataset
    :return: Resized dataset
    """
    dataset = get_dataset(raster)
    bounds_ul = [transform[0], transform[3]]
    bounds_lr = [transform[0] + (transform[1] * dimensions[0]) + (transform[2] * dimensions[1]),
            transform[3] + (transform[4] * dimensions[0]) + (transform[5] * dimensions[1])]
    bounds = bounds_ul + bounds_lr
    datatype = dataset.GetRasterBand(1).DataType
    resized_ds = gdal.GetDriverByName('MEM').Create('', dimensions[0], dimensions[1],  dataset.RasterCount, datatype)
    for i in range(1, resized_ds.RasterCount+1):
        nodatavalue = dataset.GetRasterBand(i).GetNoDataValue()
        resized_band = resized_ds.GetRasterBand(i)
        resized_arr = resized_band.ReadAsArray()
        resized_arr[resized_arr == 0] = nodatavalue
        resized_band.WriteArray(resized_arr)
        resized_band.SetNoDataValue(nodatavalue)

    resized_ds.SetGeoTransform(transform)
    resized_ds.SetProjection(projection)

    gdal.ReprojectImage(dataset, resized_ds)
    return resized_ds


def gdal_clip(raster_input, raster_output, polygon_json, nodata=-32768):
    """
    This function will subset a raster by a vector polygon.
    Adapted from the GDAL/OGR Python Cookbook at
    https://pcjericks.github.io/py-gdalogr-cookbook
    :param raster_input: raster input filepath
    :param raster_output: raster output filepath
    :param polygon_json: polygon as geojson string
    :param nodata: nodata value for output raster file
    :return:
    """

    def image_to_array(i):
        """
        Converts a Python Imaging Library array to a
        gdalnumeric image.
        """
        a = gdalnumeric.numpy.fromstring(i.tobytes(), 'b')
        a.shape = i.im.size[1], i.im.size[0]
        return a

    def world_to_pixel(geoMatrix, x, y):
        """
        Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
        the pixel location of a geospatial coordinate
        """
        ulX = geoMatrix[0]
        ulY = geoMatrix[3]
        xDist = geoMatrix[1]
        pixel = int((x - ulX) / xDist)
        line = int((ulY - y) / xDist)
        return (pixel, line)

    def OpenArray(array, prototype_ds=None, xoff=0, yoff=0):
        """
        EDIT: this is basically an overloaded
        version of the gdal_array.OpenArray passing in xoff, yoff explicitly
        so we can pass these params off to CopyDatasetInfo
        """
        ds = gdal.Open(gdalnumeric.GetArrayFilename(array))

        if ds is not None and prototype_ds is not None:
            if type(prototype_ds).__name__ == 'str':
                prototype_ds = gdal.Open(prototype_ds)
            if prototype_ds is not None:
                gdalnumeric.CopyDatasetInfo(prototype_ds, ds, xoff=xoff, yoff=yoff)
        return ds

    src_image = get_dataset(raster_input)
    # Load the source data as a gdalnumeric array
    src_array = src_image.ReadAsArray()
    src_dtype = src_array.dtype

    # Also load as a gdal image to get geotransform
    # (world file) info
    geo_trans = src_image.GetGeoTransform()
    nodata_values = []
    for i in range(src_image.RasterCount):
        nodata_value = src_image.GetRasterBand(i+1).GetNoDataValue()
        if not nodata_value:
            nodata_value = nodata
        nodata_values.append(nodata_value)

    # Create an OGR layer from a boundary GeoJSON geometry string
    if type(polygon_json) == dict:
        polygon_json = json.dumps(polygon_json)
    poly = ogr.CreateGeometryFromJson(polygon_json)

    # Convert the layer extent to image pixel coordinates
    min_x, max_x, min_y, max_y = poly.GetEnvelope()
    ul_x, ul_y = world_to_pixel(geo_trans, min_x, max_y)
    lr_x, lr_y = world_to_pixel(geo_trans, max_x, min_y)

    # Calculate the pixel size of the new image
    px_width = int(lr_x - ul_x)
    px_height = int(lr_y - ul_y)

    clip = src_array[ul_y:lr_y, ul_x:lr_x]

    # create pixel offset to pass to new image Projection info
    xoffset = ul_x
    yoffset = ul_y

    # Create a new geomatrix for the image
    geo_trans = list(geo_trans)
    geo_trans[0] = min_x
    geo_trans[3] = max_y

    # Map points to pixels for drawing the
    # boundary on a blank 8-bit,
    # black and white, mask image.
    raster_poly = Image.new("L", (px_width, px_height), 1)
    rasterize = ImageDraw.Draw(raster_poly)
    geometry_count = poly.GetGeometryCount()
    for i in range(0, geometry_count):
        points = []
        pixels = []
        pts = poly.GetGeometryRef(i)
        if pts.GetPointCount() == 0:
            pts = pts.GetGeometryRef(0)
        for p in range(pts.GetPointCount()):
            points.append((pts.GetX(p), pts.GetY(p)))
        for p in points:
            pixels.append(world_to_pixel(geo_trans, p[0], p[1]))
        rasterize.polygon(pixels, 0)
    mask = image_to_array(raster_poly)

    # Clip the image using the mask
    clip = gdalnumeric.numpy.choose(mask, (clip, nodata_value)).astype(src_dtype)

    gtiff_driver = gdal.GetDriverByName('GTiff')
    if gtiff_driver is None:
        raise ValueError("Can't find GeoTiff Driver")
    subset_raster = gtiff_driver.CreateCopy(
        raster_output, OpenArray(
            clip, prototype_ds=raster_input, xoff=xoffset, yoff=yoffset)
    )
    for i in range(subset_raster.RasterCount):
        band = subset_raster.GetRasterBand(i+1)
        band.SetNoDataValue(nodata_values[i])
    return subset_raster


def gdal_calc(calculation, raster_output, rasters, bands=None, nodata=None, allBands=None, output_type=None):
    """
    Adopted from GDAL 1.10 gdal_calc.py script.
    :param calculation: equation to calculate, such as A + (B / 2)
    :param raster_output: Raster file to save output as
    :param rasters: array of rasters, the number should be equal to the number of letters in calculation
    :param bands: array of band numbers, one for each raster in rasters array
    :param nodata: NoDataValue to use in output raster
    :param allBands: The
    :param output_type: data type for output raster ('Float32', 'Uint16', etc)
    :return: gdal Dataset
    """

    ndv_lookup = {'Byte': 255, 'UInt16': 65535, 'Int16': -32767, 'UInt32': 4294967293, 'Int32': -2147483647,
              'Float32': 1.175494351E-38, 'Float64': 1.7976931348623158E+308}

    # set up some lists to store data for each band
    datasets=[get_dataset(raster) for raster in rasters]
    if not bands:
        bands=[1 for raster in rasters]
    datatypes=[]
    datatype_nums=[]
    nodata_vals=[]
    dimensions=None
    alpha_list = string.uppercase[:len(rasters)]

    # loop through input files - checking dimensions
    for i, (raster, alpha, band) in enumerate(zip(datasets, alpha_list, bands)):
        raster_band = raster.GetRasterBand(band)
        datatypes.append(gdal.GetDataTypeName(raster_band.DataType))
        datatype_nums.append(raster_band.DataType)
        nodata_vals.append(raster_band.GetNoDataValue())
        # check that the dimensions of each layer are the same as the first
        if dimensions:
            if dimensions != [datasets[i].RasterXSize, datasets[i].RasterYSize]:
                datasets[i] = gdal_resize(raster,
                                          dimensions,
                                          datasets[0].GetProjection(),
                                          datasets[0].GetGeoTransform())
        else:
            dimensions = [datasets[0].RasterXSize, datasets[0].RasterYSize]

    # process allBands option
    allbandsindex=None
    allbandscount=1
    if allBands:
        allbandscount=datasets[allbandsindex].RasterCount
        if allbandscount <= 1:
            allbandsindex=None

    ################################################################
    # set up output file
    ################################################################

    # open output file exists
    # remove existing file and regenerate
    if os.path.isfile(raster_output):
        os.remove(raster_output)
    # create a new file
    logger.debug("Generating output file %s" % (raster_output))

    # find data type to use
    if not output_type:
        # use the largest type of the input files
        output_type=gdal.GetDataTypeName(max(datatype_nums))

    # create file
    output_driver = gdal.GetDriverByName('GTiff')
    output_dataset = output_driver.Create(
        raster_output, dimensions[0], dimensions[1], allbandscount,
        gdal.GetDataTypeByName(output_type))

    # set output geo info based on first input layer
    output_dataset.SetGeoTransform(datasets[0].GetGeoTransform())
    output_dataset.SetProjection(datasets[0].GetProjection())

    if nodata is None:
        nodata = ndv_lookup[output_type]

    for i in range(1, allbandscount+1):
        output_band = output_dataset.GetRasterBand(i)
        output_band.SetNoDataValue(nodata)
        # write to band
        output_band = None

    ################################################################
    # find block size to chop grids into bite-sized chunks
    ################################################################

    # use the block size of the first layer to read efficiently
    block_size = datasets[0].GetRasterBand(bands[0]).GetBlockSize();
    # store these numbers in variables that may change later
    n_x_valid = block_size[0]
    n_y_valid = block_size[1]
    # find total x and y blocks to be read
    n_x_blocks = int((dimensions[0] + block_size[0] - 1) / block_size[0])
    n_y_blocks = int((dimensions[1] + block_size[1] - 1) / block_size[1])
    buffer_size = block_size[0]*block_size[1]

    ################################################################
    # start looping through each band in allbandscount
    ################################################################

    for band_num in range(1, allbandscount+1):

        ################################################################
        # start looping through blocks of data
        ################################################################

        # loop through X-lines
        for x in range(0, n_x_blocks):

            # in the rare (impossible?) case that the blocks don't fit perfectly
            # change the block size of the final piece
            if x == n_x_blocks-1:
                n_x_valid = dimensions[0] - x * block_size[0]
                buffer_size = n_x_valid*n_y_valid

            # find X offset
            x_offset = x*block_size[0]

            # reset buffer size for start of Y loop
            n_y_valid = block_size[1]
            buffer_size = n_x_valid*n_y_valid

            # loop through Y lines
            for y in range(0, n_y_blocks):
                # change the block size of the final piece
                if y == n_y_blocks-1:
                    n_y_valid = dimensions[1] - y * block_size[1]
                    buffer_size = n_x_valid*n_y_valid

                # find Y offset
                y_offset = y*block_size[1]

                # create empty buffer to mark where nodata occurs
                nodatavalues = numpy.zeros(buffer_size)
                nodatavalues.shape=(n_y_valid, n_x_valid)

                # fetch data for each input layer
                for i, alpha in enumerate(alpha_list):

                    # populate lettered arrays with values
                    if allbandsindex is not None and allbandsindex == i:
                        this_band=band_num
                    else:
                        this_band=bands[i]
                    band_vals = BandReadAsArray(datasets[i].GetRasterBand(this_band),
                                                xoff=x_offset,
                                                yoff=y_offset,
                                                win_xsize=n_x_valid,
                                                win_ysize=n_y_valid)

                    # fill in nodata values
                    nodatavalues = 1*numpy.logical_or(nodatavalues==1, band_vals == nodata_vals[i])

                    # create an array of values for this block
                    exec("%s=band_vals" %alpha)
                    band_vals=None

                # try the calculation on the array blocks
                try:
                    calc_result = eval(calculation)
                except:
                    logger.error("evaluation of calculation %s failed" % calculation)
                    raise

                # propogate nodata values
                # (set nodata cells to zero then add nodata value to these cells)
                calc_result = ((1*(nodatavalues==0))*calc_result) + (nodata*nodatavalues)

                # write data block to the output file
                output_band=output_dataset.GetRasterBand(band_num)
                BandWriteArray(output_band, calc_result, xoff=x_offset, yoff=y_offset)

    return output_dataset


def get_dataset(object):
    """
    Given an object, try returning a GDAL Dataset
    :param object:
    :return:
    """
    if type(object).__name__ == 'Dataset':
        return object
    else:
        return gdal.Open(object, gdalconst.GA_ReadOnly)
