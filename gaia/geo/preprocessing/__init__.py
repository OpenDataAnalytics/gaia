
from gaia.geo.preprocessing.pandas_processes import *
from gaia.geo.preprocessing.gdal_processes import *

from gaia.process_registry import compute


def crop (inputs=[], args={}):
    return compute('crop', inputs=inputs, args=args)

# def centroid(inputs=[], args={}):
#     return compute('centroid', inputs=inputs, args=args)

# def intersection(inputs=[], args={}):
#     return compute('intersection', inputs=inputs, args=args)

# def within(inputs=[], args=[]):
#     return compute('within', inputs=inputs, args=args)

# def subset(inputs=[], args=[]):
#     return compute('subset', inputs=inputs, args=args)
