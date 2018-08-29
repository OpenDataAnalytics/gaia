
from gaia.preprocess.pandas_processes import *
from gaia.preprocess.gdal_processes import *

from gaia.process_registry import compute


# def crop (inputs=[], args={}):
def crop (*args, **kwargs):
    return compute('crop', inputs=list(args), args=kwargs)

# def centroid(inputs=[], args={}):
#     return compute('centroid', inputs=inputs, args=args)

# def intersection(inputs=[], args={}):
#     return compute('intersection', inputs=inputs, args=args)

# def within(inputs=[], args=[]):
#     return compute('within', inputs=inputs, args=args)

# def subset(inputs=[], args=[]):
#     return compute('subset', inputs=inputs, args=args)
