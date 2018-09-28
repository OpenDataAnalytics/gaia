from __future__ import absolute_import, division, print_function
from builtins import (
    bytes, str, open, super, range, zip, round, input, int, pow, object
)
from future.standard_library import install_aliases
install_aliases()
import sys
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
def compute_crop2(inputs=[], args_dict={}):
    """
    Runs the subset computation on girder
    """
    datasets = inputs[0]
    geometry = inputs[1]
    # print('datasets: ', datasets)
    # print('geometry:', geometry)
    # print('args_dict:', args_dict)

    # if not isinstance(input, collections.Iterable):
    #     datasets = [datasets]

    # # Verify that all datasets are girder objects
    # for dataset in datasets:
    #     assert isinstance(dataset,GirderDataObject), 'Some input datasets are NOT girder objects'

    # Current support is single dataset
    assert isinstance(datasets,GirderDataObject), 'Input dataset is NOT a single GaiaDataObject'

    results_folder_id = '5bae2a52e44298008d78ac92'  # hard code for now
    filename = args_dict.get('name', 'crop2_output.tif')
    #print(filename)

    from gaia.io.girder_interface import GirderInterface
    gc = GirderInterface._get_girder_client()

    # Check for existing file (and delete)
    result = gc.listItem(results_folder_id, name=filename)
    # print(result)
    for item in result:
        item_path = 'item/{}'.format(item['_id'])
        print('Deleting existing {} file (item {})'.format(filename, item_path))
        del_result = gc.delete(item_path)
        # print(del_result)

    # Run the clip operation
    path = 'raster/clip'
    params = {
        'itemId': datasets.resource_id,
        'geometry': json.dumps(geometry),
        'name': filename,
        'folderId': results_folder_id
    }
    job = gc.get(path, parameters=params)
    # print()
    # print(job)

    import time
    path = 'job/{}'.format(job['_id'])
    status = job['status']
    for i in range(50):
        if status >= 3:
            break
        # (Using sys.stdout to skip newline at end)
        sys.stdout.write(
            '{:2d} Checking job {} status... '.format(i+1, job['_id']))
        time.sleep(1.0)
        job = gc.get(path)
        status = job['status']
        print(status)

    # Get item id of (new) output file
    result = gc.listItem(results_folder_id, name=filename)
    cropped_item = next(result)
    # print(cropped_item)

    outputDataObject = GirderDataObject(None, 'item', cropped_item['_id'])
    return outputDataObject
