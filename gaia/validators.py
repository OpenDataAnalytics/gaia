from __future__ import absolute_import, division, print_function
from builtins import (bytes, str, open, super, range, zip, round, input, int, pow, object)

import gaia.types as types
from gaia.validate_base import validate_base


# """
# Decorator for validating centroid process inputs.  This can be reused by both
# the pandas and postgis centroid implementations, while a different one would be
# required in the case of a gdal/raster centroid.
# """
# def validate_centroid(v):
#     def centroid_validator(inputs=[], args={}):
#         required_inputs = [{
#             'description': 'Line/Polygon dataset',
#             'type': types.VECTOR,
#             'max': 1
#         }]

#         optional_args = [{
#             'name': 'combined',
#             'title': 'Combined',
#             'description': 'Get centroid of features combined (default False)',
#             'type': bool,
#         }]

#         validate_base(inputs, args, required_inputs=required_inputs, optional_args=optional_args)
#         return v(inputs, args)

#     return centroid_validator


# """
# Decorator for validating intersection process inputs
# """
# def validate_intersection(v):
#     def intersection_validator(inputs=[], args={}):
#         required_inputs=[{
#             'description': 'Feature dataset',
#             'type': types.VECTOR,
#             'max': 1
#         },{
#             'description': 'Intersect dataset',
#             'type': types.VECTOR,
#             'max': 1
#         }]

#         validate_base(inputs, args, required_inputs=required_inputs)
#         return v(inputs, args)

#     return intersection_validator


"""
Decorator for validating within process inputs
"""
def validate_within(v):
    def within_validator(inputs=[], args={}):
        required_inputs = [{
            'description': 'Feature dataset',
            'type': types.VECTOR,
            'max': 1
        },{
            'description': 'Within dataset',
            'type': types.VECTOR,
            'max': 1
        }]

        validate_base(inputs, args, required_inputs=required_inputs)
        return v(inputs, args)

    return within_validator


"""
Decorator for validating subset process inputs
"""
def validate_subset(v):
    def subset_validator(inputs=[], args=[]):
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

        validate_base(inputs, args, required_inputs=required_inputs)
        return v(inputs, args)

    return subset_validator
