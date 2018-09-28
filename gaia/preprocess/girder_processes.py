from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlencode

import collections
import json

from gaia import GaiaException
from gaia.girder_data import GirderDataObject
from gaia.process_registry import register_process


@register_process('crop')
def compute_subset_girder(inputs=[], args=[]):
    """
    Runs the subset computation on girder
    """
    print('inputs: ', inputs)
    print('args:', args)

    # Verify that all inputs are girder objects
    for dataset in inputs:
        assert isinstance(dataset,GirderDataObject), 'Some input datasets are NOT girder objects'


    outputDataObject = GirderDataObject(None, 'type_undefined', 'id_undefinded')
    return outputDataObject

@register_process('crop2')
def compute_crop2(datasets, geometry, args={}):
    """
    Runs the subset computation on girder
    """
    print('datasets: ', datasets)
    print('geometry:', geometry)

    # if not isinstance(input, collections.Iterable):
    #     datasets = [datasets]

    # # Verify that all datasets are girder objects
    # for dataset in datasets:
    #     assert isinstance(dataset,GirderDataObject), 'Some input datasets are NOT girder objects'

    # Current support is single dataset
    assert isinstance(datasets,GirderDataObject), 'Input dataset is NOT a single GaiaDataObject'

    results_folder_id = '5bae2a52e44298008d78ac92'  # hard code for now
    name = args.get('name', 'makeupaname')  # uuid?

    from gaia.io.girder_interface import GirderInterface
    gc = GirderInterface._get_girder_client()
    path = 'raster/clip'
    params = {
        'itemId': datasets.resource_id,
        'geometry': json.dumps(geometry),
        'name': name,
        'folderId': results_folder_id
    }
    # reply = gc.get(path, parameters=urlencode(params))
    s = '{}?{}'.format(path,urlencode(params))
    print(s)

    reply = gc.get(s)
    print()
    print('reply:', reply)


    outputDataObject = GirderDataObject(None, 'type_undefined', 'id_undefinded')
    return outputDataObject
