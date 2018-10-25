from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)

import gaia.validators as validators
from gaia.process_registry import register_process
from gaia import GaiaException
from gaia.gaia_data import GaiaDataObject

from geopandas import GeoDataFrame
from geopandas import GeoSeries


def validate_pandas(v):
    """
    Since the base validate method we import does most of the work in a fairly
    generic way, this function only needs to add a little bit to that: make
    sure the inputs contain geopandas dataframe.  Additionally, all the
    processes defined in this module can re-use the same validate method.
    """
    def validator(inputs=[], args={}):
        # First should check if input is compatible w/ pandas computation
        if type(inputs[0].get_data()) is not GeoDataFrame:
            raise GaiaException('pandas process requires a GeoDataFrame')

        # Otherwise call up the chain to let parent do common validation
        return v(inputs, args)

    return validator


@register_process('crop')
@validators.validate_within
@validate_pandas
def crop_pandas(inputs=[], args={}):
    """
    Calculate the within process using pandas GeoDataFrames

    :return: within result as a GeoDataFrame
    """
    first, second = inputs[0], inputs[1]
    if first.get_epsg() != second.get_epsg():
        second.reproject(epsg=first.get_epsg())
    first_df, second_df = first.get_data(), second.get_data()
    first_within = first_df[first_df.geometry.within(
        second_df.geometry.unary_union)]

    outputDataObject = GaiaDataObject(first._reader)
    outputDataObject.set_data(first_within)
    return outputDataObject


# """
# These methods can be very small and focused on doing only one thing: given
# an array of inputs and possibly some arguments, do the computation and
# return something (maybe a GaiaDataObject, or perhaps just a number)
# """
# @register_process('centroid')
# @validate_centroid
# @validate_pandas
# def compute_centroid_pandas(inputs=[], args={}):
#     """
#     Calculate the centroid using pandas GeoDataFrames

#     :return: centroid as a GeoDataFrame
#     """

#     # Only worry about a pandas version of the compute method
#     print('compute_centroid_pandas')

#     df_in = inputs[0].get_data()
#     df = GeoDataFrame(df_in.copy(), geometry=df_in.geometry.name)
#     if 'combined' in args and args['combined']:
#         gs = GeoSeries(df.geometry.unary_union.centroid,
#                        name=df_in.geometry.name)
#         output_data = GeoDataFrame(gs)
#     else:
#         df[df.geometry.name] = df.geometry.centroid
#         output_data = df

#     # Now processes need to create and return a GaiaDataObject, whose
#     # "data" member contains the actual data
#     outputDataObject = GaiaDataObject()
#     outputDataObject.set_data(output_data)

#     return outputDataObject


# """
# Do a pandas intersection
# """
# @register_process('intersection')
# @validate_intersection
# @validate_pandas
# def compute_intersection_pandas(inputs=[], args={}):
#     print('compute_intersection_pandas')
#     return None
