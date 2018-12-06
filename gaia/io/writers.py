from __future__ import absolute_import, division, print_function
import os

try:
    import osr
except ImportError:
    from osgeo import osr

import gdal
import geopandas


from gaia import types
from gaia.gaia_data import GaiaDataObject
from gaia.util import GaiaException

# Map of <file-extension, driver-name> for GeoPandas
GEOPANDAS_DRIVERS = {
    '.geojson': 'GeoJSON',
    '.json': 'GeoJSON',
    '.shp': 'ESRI Shapefile'
}

# Map of <file-extension, driver-name> for GDAL
GDAL_DRIVERS = {
    '.geotiff': 'GTiff',
    '.jp2': 'JP2OpenJPEG',
    '.jp2k': 'JP2OpenJPEG',
    '.ntf': 'NITF',
    '.tif': 'GTiff'
}


def write_gaia_object(gaia_object, filename, **options):
    if gaia_object.__class__.__name__ == 'GirderDataObject':
        raise GaiaException('Writing not supported for GirderDataObject')

    data_type = gaia_object._getdatatype()
    if data_type == types.VECTOR:
        return write_vector_object(gaia_object, filename, **options)
    elif data_type == types.RASTER:
        return write_raster_object(gaia_object, filename, **options)
    else:
        raise GaiaException('Unsupported data type {}'.format(data_type))


def write_vector_object(gaia_object, filename, **options):
    # Delete existing file (if any)
    if os.path.exists(filename):
        os.remove(filename)

    data = gaia_object.get_data()
    ext = os.path.splitext(filename)[1]
    if ext == '':
        ext = '.geojson'  # default
    driver = GEOPANDAS_DRIVERS.get(ext)
    if driver is None:
        raise GaiaException('Unsupported file extension {}'.format(ext))
    data.to_file(filename, driver, **options)


def write_raster_object(gaia_object, filename, **options):
    # Delete existing file (if any)
    if os.path.exists(filename):
        os.remove(filename)

    ext = os.path.splitext(filename)[1]
    if ext == '':
        ext = '.tif'  # default
    driver_name = GDAL_DRIVERS.get(ext)
    if driver_name is None:
        raise GaiaException('Unsupported file extension {}'.format(ext))

    # Have to create copy of dataset in order to write to file
    driver = gdal.GetDriverByName(driver_name)
    if driver is None:
        raise GaiaException('GDAL driver {} not found'.format(driver_name))

    gdal_dataset = gaia_object.get_data()
    output_dataset = driver.CreateCopy(filename, gdal_dataset, strict=0)
    # Setting the dataset to None causes the write to disk
    # Add # noqa comment to ignore flake8 error that variable isn't used
    output_dataset = None  # writes to disk  # noqa: F841
