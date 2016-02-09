import json
from geopandas import GeoDataFrame
from osgeo import gdal, gdalnumeric, ogr, osr
from PIL import Image, ImageDraw


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
    src_ds = get_Dataset(src)

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


def gdal_clip(raster_input, raster_output, polygon_json, nodata=-32768):
    """
    This function will subset a raster by a vector polygon.
    Adapted from the GDAL/OGR Python Cookbook at
    https://pcjericks.github.io/py-gdalogr-cookbook
    :param raster_file: Image to be subset
    :param poly_json: A JSON string representation of a polygon
    :return:
    """

    def image_to_array(i):
        """
        Converts a Python Imaging Library array to a
        gdalnumeric image.
        """
        a=gdalnumeric.fromstring(i.tobytes(),'b')
        a.shape=i.im.size[1], i.im.size[0]
        return a

    def array_to_image(a):
        """
        Converts a gdalnumeric array to a
        Python Imaging Library Image.
        """
        i=Image.frombytes('L',(a.shape[1],a.shape[0]),
                (a.astype('b')).tobytes())
        return i

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

    def OpenArray( array, prototype_ds = None, xoff=0, yoff=0 ):
        """
        EDIT: this is basically an overloaded
        version of the gdal_array.OpenArray passing in xoff, yoff explicitly
        so we can pass these params off to CopyDatasetInfo
        """
        ds = gdal.Open( gdalnumeric.GetArrayFilename(array) )

        if ds is not None and prototype_ds is not None:
            if type(prototype_ds).__name__ == 'str':
                prototype_ds = gdal.Open( prototype_ds )
            if prototype_ds is not None:
                gdalnumeric.CopyDatasetInfo( prototype_ds, ds, xoff=xoff, yoff=yoff )
        return ds

    src_image = get_Dataset(raster_input)
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
    xoffset =  ul_x
    yoffset =  ul_y

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
            #MultiPolygon
            pts = pts.GetGeometryRef(0)
        for p in range(pts.GetPointCount()):
          points.append((pts.GetX(p), pts.GetY(p)))
        for p in points:
          pixels.append(world_to_pixel(geo_trans, p[0], p[1]))
        rasterize.polygon(pixels, 0)
    mask = image_to_array(raster_poly)

    # Clip the image using the mask
    clip = gdalnumeric.choose(mask, (clip, nodata_value)).astype(src_dtype)

    gtiff_driver = gdal.GetDriverByName( 'GTiff' )
    if gtiff_driver is None:
        raise ValueError("Can't find GeoTiff Driver")
    subset_raster = gtiff_driver.CreateCopy(raster_output,
        OpenArray(clip, prototype_ds=raster_input, xoff=xoffset, yoff=yoffset)
    )
    for i in range(subset_raster.RasterCount):
        band = subset_raster.GetRasterBand(i+1)
        band.SetNoDataValue(nodata_values[i])
    return subset_raster


def get_Dataset(object):
    """
    Given an object, try returning a GDAL Dataset
    :param object:
    :return:
    """
    if type(object).__name__ == 'Dataset':
        return object
    else:
        return gdal.Open(object)


