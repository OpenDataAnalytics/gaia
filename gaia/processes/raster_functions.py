import logging
from math import ceil
from rasterio._io import Resampling
from rasterio.rio.helpers import resolve_inout
import rasterio
from rasterio import crs
from rasterio.transform import Affine
from rasterio.warp import (reproject, calculate_default_transform,
   transform_bounds)
from gaia.core import GaiaException

__author__ = 'mbertrand'

MAX_OUTPUT_WIDTH = 100000
MAX_OUTPUT_HEIGHT = 100000


def warp(files, output, driver, like=None, dst_crs='EPSG:3857', dimensions=None,
         src_bounds=None, x_dst_bounds=None, bounds=None, res=None,
         resampling='nearest', threads=2, force_overwrite=False,
         creation_options=None):
    """
    Warp a raster dataset.
    """

    output, files = resolve_inout(
        files=files, output=output, force_overwrite=force_overwrite)

    resampling = Resampling[resampling]  # get integer code for method

    if not len(res):
        # Click sets this as an empty tuple if not provided
        res = None
    else:
        # Expand one value to two if needed
        res = (res[0], res[0]) if len(res) == 1 else res

    with rasterio.drivers():
        with rasterio.open(files[0]) as src:
            l, b, r, t = src.bounds
            out_kwargs = src.meta.copy()
            out_kwargs['driver'] = driver

            # Sort out the bounds options.
            src_bounds = bounds or src_bounds
            dst_bounds = x_dst_bounds
            if src_bounds and dst_bounds:
                raise GaiaException(
                    "Source and destination bounds may not be specified "
                    "simultaneously.")

            if like:
                with rasterio.open(like) as template_ds:
                    dst_crs = template_ds.crs
                    dst_transform = template_ds.affine
                    dst_height = template_ds.height
                    dst_width = template_ds.width

            elif dst_crs:
                try:
                    dst_crs = crs.from_string(dst_crs)
                except ValueError:
                    raise GaiaException("invalid crs format.")

                if dimensions:
                    # Calculate resolution appropriate for dimensions
                    # in target.
                    dst_width, dst_height = dimensions
                    xmin, ymin, xmax, ymax = transform_bounds(src.crs, dst_crs,
                                                              *src.bounds)
                    dst_transform = Affine(
                        (xmax - xmin) / float(dst_width),
                        0, xmin, 0,
                        (ymin - ymax) / float(dst_height),
                        ymax
                    )

                elif src_bounds or dst_bounds:
                    if not res:
                        raise GaiaException( "Required when using --bounds.")

                    if src_bounds:
                        xmin, ymin, xmax, ymax = transform_bounds(
                            src.crs, dst_crs, *src_bounds)
                    else:
                        xmin, ymin, xmax, ymax = dst_bounds

                    dst_transform = Affine(res[0], 0, xmin, 0, -res[1], ymax)
                    dst_width = max(int(ceil((xmax - xmin) / res[0])), 1)
                    dst_height = max(int(ceil((ymax - ymin) / res[1])), 1)

                else:
                    dst_transform, dst_width, dst_height = calculate_default_transform(
                        src.crs, dst_crs, src.width, src.height, *src.bounds,
                        resolution=res)

            elif dimensions:
                # Same projection, different dimensions, calculate resolution.
                dst_crs = src.crs
                dst_width, dst_height = dimensions
                dst_transform = Affine(
                    (r - l) / float(dst_width),
                    0, l, 0,
                    (b - t) / float(dst_height),
                    t
                )

            elif src_bounds or dst_bounds:
                # Same projection, different dimensions and possibly
                # different resolution.
                if not res:
                    res = (src.affine.a, -src.affine.e)

                dst_crs = src.crs
                xmin, ymin, xmax, ymax = (src_bounds or dst_bounds)
                dst_transform = Affine(res[0], 0, xmin, 0, -res[1], ymax)
                dst_width = max(int(ceil((xmax - xmin) / res[0])), 1)
                dst_height = max(int(ceil((ymax - ymin) / res[1])), 1)

            elif res:
                # Same projection, different resolution.
                dst_crs = src.crs
                dst_transform = Affine(res[0], 0, l, 0, -res[1], t)
                dst_width = max(int(ceil((r - l) / res[0])), 1)
                dst_height = max(int(ceil((t - b) / res[1])), 1)

            else:
                dst_crs = src.crs
                dst_transform = src.affine
                dst_width = src.width
                dst_height = src.height

            # When the bounds option is misused, extreme values of
            # destination width and height may result.
            if (dst_width < 0 or dst_height < 0 or
                        dst_width > MAX_OUTPUT_WIDTH or
                        dst_height > MAX_OUTPUT_HEIGHT):
                raise GaiaException(
                    "Invalid output dimensions: {0}.".format(
                        (dst_width, dst_height)))

            out_kwargs.update({
                'crs': dst_crs,
                'transform': dst_transform,
                'affine': dst_transform,
                'width': dst_width,
                'height': dst_height
            })

            out_kwargs.update(**creation_options)

            with rasterio.open(output, 'w', **out_kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.affine,
                        src_crs=src.crs,
                        # src_nodata=#TODO
                        dst_transform=out_kwargs['transform'],
                        dst_crs=out_kwargs['crs'],
                        # dst_nodata=#TODO
                        resampling=resampling,
                        num_threads=threads)