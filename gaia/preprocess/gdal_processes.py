from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from gaia import GaiaException
from gaia.gaia_data import GDALDataObject
from gaia.validators import validate_subset
from gaia.process_registry import register_process
from gaia.geo.gdal_functions import gdal_clip
from gaia.io.gdal_reader import GaiaGDALReader
import gaia.types



def validate_gdal(v):
    """
    Rely on the base validate method for the bulk of the work, just make
    sure the inputs are gdal-compatible.
    """
    def validator(inputs=[], args=[]):
        # FIXME: we should check we have a specific gdal type input also
        return v(inputs, args)
    return validator


@register_process('crop')
@validate_subset
@validate_gdal
def compute_subset_gdal(inputs=[], args=[]):
    """
    Runs the subset computation, creating a raster dataset as output.
    """
    raster, clip = inputs[0], inputs[1]
    raster_img = raster.get_data()

    if clip.get_epsg() != raster.get_epsg():
        clip.reproject(raster.get_epsg())

    clip_json = clip.get_data().geometry.unary_union.__geo_interface__

    # Passing "None" as second arg instead of a file path.  This tells gdal_clip
    # not to write the output dataset to a tiff file on disk
    output_dataset = gdal_clip(raster_img, None, clip_json)

    # Copy data to new GDALDataObject
    outputDataObject = GDALDataObject()
    outputDataObject.set_data(output_dataset)
    outputDataObject._datatype = gaia.types.RASTER

    # Instantiate temporary reader to (only) parse metadata
    reader = GaiaGDALReader('internal.tif')
    meta = reader.load_metadata(outputDataObject)

    return outputDataObject
