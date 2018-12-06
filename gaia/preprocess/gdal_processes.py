from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

from gaia import GaiaException
from gaia.gaia_data import GDALDataObject
from gaia.validators import validate_subset
from gaia.process_registry import register_process
from gaia.geo.gdal_functions import gdal_clip
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

    outputDataObject = GDALDataObject()
    outputDataObject.set_data(output_dataset)
    outputDataObject._datatype = gaia.types.RASTER

    # print('input meta: {}'.format(raster.get_metadata()))

    # Get corner points
    gt = output_dataset.GetGeoTransform()
    if gt is None:
        raise Exception('Cannot compute corners - dataset has no geo transform')
    num_cols = output_dataset.RasterXSize
    num_rows = output_dataset.RasterYSize
    corners = list()
    for px in [0, num_cols]:
        for py in [0, num_rows]:
            x = gt[0] + px*gt[1] + py*gt[2]
            y = gt[3] + px*gt[4] + py*gt[5]
            corners.append([x, y])

    # if as_lonlat:
    #     spatial_ref = osr.SpatialReference()
    #     spatial_ref.ImportFromWkt(self.get_wkt_string())
    #     corners = self._convert_to_lonlat(corners, spatial_ref)

    xvals = [c[0] for c in corners]
    yvals = [c[1] for c in corners]
    xmin = min(xvals)
    ymin = min(yvals)
    xmax = max(xvals)
    ymax = max(yvals)
    coords = [[
        [xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]
    ]]
    metadata = {
        'bounds': {
            'coordinates': coords
        },
        'height': output_dataset.RasterYSize,
        'width': output_dataset.RasterXSize
    }
    print('metadata: {}'.format(metadata))
    outputDataObject.set_metadata(metadata)

    return outputDataObject
